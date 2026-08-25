# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Ctrl+C (SIGINT) handling.

On Ctrl+C, the terminal sends SIGINT to the whole foreground process group,
i.e. to Python and the Tcl tool alike. Each scenario below runs in a child
Python process with its own process group; once the scenario reports READY,
SIGINT is sent to that group, like the terminal would do.

The Tcl tool's reaction to SIGINT is modelled with test-notcl-tclsh:

- default: the tool dies (plain tclsh behaviour).
- ignore_sigint + after: the tool survives, the command runs to completion.
- ignore_sigint + exec sleep: the tool survives, the command fails with a
  Tcl error ("child killed: interrupt"), like a tool that aborts its
  current command on SIGINT.
"""

import os
import re
import sys
import select
import signal
import subprocess
import time
from pathlib import Path
from textwrap import dedent

import pytest

from .test_custom_tclsh import CustomTclsh

NOTCL_ROOT = Path(__file__).resolve().parents[2]

HINT = "[notcl] Info: SIGINT received, waiting for the Tcl tool"

def run_scenario(code, on_line, timeout=20):
    """
    Runs scenario code in a child Python process in its own process group.
    on_line(proc, line) is called for every line of combined stdout/stderr
    output and can react (e.g. send SIGINT to the group).
    Returns (output, returncode).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(NOTCL_ROOT)

    code_prelude = dedent("""\
        import sys, os, time
        from notcl import TclTool, TclError, ChildProcessEarlyExit

        class CustomTclsh(TclTool):
            def cmdline(self):
                return ["test-notcl-tclsh", self.script_name()]

        def report(*args):
            print("SCENARIO:", *args, flush=True)
        """)

    p = subprocess.Popen([sys.executable, "-c", code_prelude + code],
        env=env, start_new_session=True, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    fd = p.stdout.fileno()
    buf = b""
    output = ""
    deadline = time.monotonic() + timeout
    try:
        while True:
            rdready, _, _ = select.select([fd], [], [], max(0, deadline - time.monotonic()))
            if not rdready:
                pytest.fail(f"scenario timed out; output so far:\n{output}")
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.decode(errors="replace") + "\n"
                output += line
                on_line(p, line)
        rc = p.wait(timeout=5)
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
    return output, rc

def sigint_on_ready(p, line):
    if line.startswith("SCENARIO: READY"):
        time.sleep(0.5) # give the Tcl side time to start the command
        os.killpg(p.pid, signal.SIGINT)

def assert_clean(output):
    assert "AssertionError" not in output
    assert "Traceback" not in output
    assert "couldn't open" not in output # Tcl side error after Python teardown

def test_tool_aborts_command_with_error():
    CustomTclsh.require()
    output, rc = run_scenario(dedent("""\
        with CustomTclsh(log_fancy=False) as t:
            t.ignore_sigint()
            report("PID", t.tcl_tool.proc.pid)
            report("READY")
            try:
                t.exec("sleep", "5")
                report("NO_ERROR")
            except TclError as e:
                report("TCLERROR", e)
            report("EXPR", t.expr(1, "+", 1))
        report("DONE")
        """), sigint_on_ready)
    assert "SCENARIO: TCLERROR child killed: interrupt\n" in output
    assert "SCENARIO: EXPR 2\n" in output # tool still usable afterwards
    assert "SCENARIO: DONE\n" in output
    assert output.count(HINT) == 1
    pid = re.search(r"^SCENARIO: PID (\d+)$", output, re.MULTILINE).group(1)
    assert f"terminate it (pid {pid})" in output # hint names the tool's pid
    assert rc == 0
    assert_clean(output)

def test_tool_ignores_sigint():
    CustomTclsh.require()
    output, rc = run_scenario(dedent("""\
        with CustomTclsh(log_fancy=False) as t:
            t.ignore_sigint()
            report("READY")
            try:
                t.after(2000)
                report("NO_INTERRUPT")
            except KeyboardInterrupt:
                report("KEYBOARDINTERRUPT")
            report("EXPR", t.expr(1, "+", 1))
        report("DONE")
        """), sigint_on_ready)
    assert "SCENARIO: KEYBOARDINTERRUPT\n" in output # Ctrl+C is not lost
    assert "SCENARIO: EXPR 2\n" in output
    assert "SCENARIO: DONE\n" in output
    assert output.count(HINT) == 1
    assert rc == 0
    assert_clean(output)

def test_tool_ignores_sigint_interact():
    # With interact=True, the KeyboardInterrupt raised after the ignored
    # SIGINT must end the session like any other exception (abort_on_error),
    # instead of handing the user over to the tool's prompt.
    CustomTclsh.require()
    output, rc = run_scenario(dedent("""\
        try:
            with CustomTclsh(interact=True, log_fancy=False) as t:
                t.ignore_sigint()
                report("READY")
                t.after(2000)
                report("NO_INTERRUPT")
        except KeyboardInterrupt:
            report("KEYBOARDINTERRUPT")
        report("DONE")
        """), sigint_on_ready)
    assert "SCENARIO: KEYBOARDINTERRUPT\n" in output
    assert "SCENARIO: DONE\n" in output
    assert "Please exit Tcl tool" not in output # no interactive session
    assert rc == 0
    assert_clean(output)

def test_tool_dies():
    CustomTclsh.require()
    output, rc = run_scenario(dedent("""\
        try:
            with CustomTclsh() as t:
                report("READY")
                t.after(2000)
                report("NO_EXCEPTION")
        except ChildProcessEarlyExit:
            report("EARLY_EXIT")
        report("DONE")
        """), sigint_on_ready)
    assert "SCENARIO: EARLY_EXIT\n" in output
    assert "SCENARIO: DONE\n" in output
    assert rc == 0
    assert_clean(output)

def test_sigint_during_startup():
    # Ctrl+C while the tool is still starting up (before TclHello) must not
    # break off the handshake: the tool is left alone, and once it is up,
    # KeyboardInterrupt is raised and the tool is quit regularly.
    output, rc = run_scenario(dedent("""\
        class SlowTclsh(TclTool):
            def cmdline(self):
                # Launcher ignores SIGINT (so the tool survives the Ctrl+C
                # of this test) and takes its time before starting the tool.
                return ["sh", "-c", 'trap "" INT; sleep 2; exec tclsh "$1"',
                    "sh", self.script_name()]
        tool = SlowTclsh(log_fancy=False)
        report("READY")
        try:
            with tool as t:
                report("STARTED")
        except KeyboardInterrupt:
            report("KEYBOARDINTERRUPT")
        report("CHILD_RC", tool.proc.returncode)
        report("DONE")
        """), sigint_on_ready)
    assert "SCENARIO: STARTED\n" not in output
    assert "SCENARIO: KEYBOARDINTERRUPT\n" in output
    assert "SCENARIO: CHILD_RC 0\n" in output # tool was started and quit regularly
    assert "SCENARIO: DONE\n" in output
    assert rc == 0
    assert_clean(output)

def test_handle_sigint_disabled():
    CustomTclsh.require()
    output, rc = run_scenario(dedent("""\
        try:
            with CustomTclsh(handle_sigint=False) as t:
                tool = t.tcl_tool
                t.ignore_sigint()
                report("READY")
                t0 = time.monotonic()
                t.after(5000)
                report("NO_EXCEPTION")
        except KeyboardInterrupt:
            report("KEYBOARDINTERRUPT", "fast" if time.monotonic() - t0 < 2 else "slow")
        report("CHILD_RC", tool.proc.returncode)
        report("DONE")
        """), sigint_on_ready)
    assert "SCENARIO: KEYBOARDINTERRUPT fast\n" in output # raised immediately
    assert f"SCENARIO: CHILD_RC {-signal.SIGTERM}\n" in output # child terminated
    assert "SCENARIO: DONE\n" in output
    assert HINT not in output
    assert rc == 0
    assert_clean(output)
