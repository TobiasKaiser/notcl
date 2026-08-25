# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import pytest
import subprocess
from pathlib import Path
from textwrap import dedent
from .. import TclTool, TclError, ChildProcessEarlyExit

class Tclsh(TclTool):
    def cmdline(self):
        return ["tclsh", self.script_name()]

def test_set_string():
    with Tclsh() as t:
        t.set("myvar", "ThisIsATest")
        v=t.set("myvar")
        assert str(v) == "ThisIsATest"

def test_set_int():
    with Tclsh() as t:
        t.set("myvar", 123459)
        v=t.set("myvar")
        assert int(v) == 123459

def test_set_float():
    with Tclsh() as t:
        t.set("myvar", 3.14)
        v=t.set("myvar")
        assert abs(float(v) - 3.14) < 0.01 


def test_expr():
    with Tclsh() as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11

def test_list_of_strings():
    with Tclsh() as t:
        v=t.lreverse(["one", "two", "three"])
        assert str(v).split(" ") == ["three", "two", "one"]

def test_list_of_ints():
    with Tclsh() as t:
        v=t.lreverse([5,6,7])
        assert list(map(int, str(v).split(" "))) == [7,6,5]


def test_dict():
    with Tclsh() as t:
        v=t.dict("merge", {"key1":"value1"}, {"key2":"value2", "key3":"value3"})
        assert str(v).split(" ") == ["key1", "value1", "key2", "value2", "key3", "value3"]

def test_expr_log_commands(capfd):
    with Tclsh(log_commands=True) as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11
    cap = capfd.readouterr()
    assert cap.out == "[notcl] Cmd: expr {9} {+} {3} {*} {11}\n"
    assert cap.err == ""

def test_expr_log_commands_disabled(capfd):
    with Tclsh(log_commands=False) as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11
    cap = capfd.readouterr()
    assert cap.out == ""
    assert cap.err == ""

class TclshStdoutToFile(Tclsh):
    """
    Runs tclsh with (only) its stdout redirected into a file. This
    separates output written by the Tcl process from output written by
    Python, which capfd would otherwise capture together.
    """
    def __init__(self, stdout_file, **kwargs):
        super().__init__(**kwargs)
        self.stdout_file = str(stdout_file)

    def cmdline(self):
        return ["sh", "-c", 'exec tclsh "$1" > "$2"', "sh",
            self.script_name(), self.stdout_file]

def test_log_commands_written_by_tcl_process(capfd, tmp_path):
    # The Cmd: line must be written by the Tcl process to its own stdout, so
    # that it ends up in log files that a Tcl tool creates from its output.
    # It must precede the output produced by the command itself.
    stdout_file = tmp_path / "tool_stdout.log"
    with TclshStdoutToFile(stdout_file, log_commands=True) as t:
        t.puts("hello from tcl")
    assert stdout_file.read_text() == dedent("""\
        [notcl] Cmd: puts {hello from tcl}
        hello from tcl
        """)
    cap = capfd.readouterr()
    assert cap.out == ""
    assert cap.err == ""

def test_log_commands_and_retvals_ordering():
    # Cmd: lines are written by the Tcl process, Result: lines by Python.
    # They must appear in order even if stdout is not a terminal, i.e. when
    # Python's stdout is block-buffered. pytest's capfd is unbuffered, so this
    # is run in a child Python process with stdout redirected into a pipe.
    code = dedent("""\
        from notcl import TclTool
        class Tclsh(TclTool):
            def cmdline(self):
                return ["tclsh", self.script_name()]
        with Tclsh(log_commands=True, log_retvals=True, log_fancy=False) as t:
            t.expr(1, '+', 1)
            t.expr(2, '*', 3)
        """)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
    res = subprocess.run([sys.executable, "-c", code], env=env,
        capture_output=True, text=True, check=True)
    assert res.stdout == dedent("""\
        [notcl] Cmd: expr {1} {+} {1}
        [notcl] Result: 2
        [notcl] Cmd: expr {2} {*} {3}
        [notcl] Result: 6
        """)
    assert res.stderr == ""

def test_explicit_ref():
    with Tclsh() as t:
        v1=t("expr 44 - 2")
        v2=t(f"expr {v1.ref_str()} / 2")
        assert int(v2) == 21
        v3=t(f"format Hello%i {v2.ref_str()}")
        assert str(v3) == "Hello21"

def test_implicit_ref():
    with Tclsh() as t:
        v1=t.expr(44, '-', 2)
        v2=t.expr(v1, '/', 2) 
        assert int(v2) == 21
        v3=t.format("Hello%i", v2)
        assert str(v3) == "Hello21"

def test_tclerror():
    with Tclsh() as t:
        with pytest.raises(TclError):
            t.expr("*", "+")

        with pytest.raises(TclError):
            t("does_not_exist")

        v=t.expr(1, '+', 1)
        assert int(v)==2

def test_lists():
    with Tclsh() as t:
        ret = t.list(1,2,3)
        assert str(ret) == '1 2 3'

def test_boolargs():
    with Tclsh() as t:
        ret = t.list(myarg=True)
        assert str(ret) == '-myarg'

        ret = t.list(myarg=False)
        assert str(ret) == ''

def test_repr():
    with Tclsh() as t:
        ret = t.list("hello", "world")
        assert repr(ret) == "Tcl'hello world'"

def test_child_terminates_nonzero():
    reaches1 = False
    reaches2 = False
    with pytest.raises(ChildProcessEarlyExit):
        with Tclsh() as t:
            reaches1 = True
            v=t.exit(1)
            reaches2 = True

    assert reaches1
    assert not reaches2

def test_child_terminates_zero():
    reaches1 = False
    reaches2 = False
    with pytest.raises(ChildProcessEarlyExit):
        with Tclsh() as t:
            reaches1 = True
            v=t.exit(0)
            reaches2 = True

    assert reaches1
    assert not reaches2

def test_child_fails_to_start():
    # The tool dies before it ever runs notcl.tcl (e.g. invalid command line
    # args), so it never opens the sentinel pipe. This must be detected
    # anyway, not hang. Runs in a child process with a timeout.
    from .test_sigint import run_scenario
    output, rc = run_scenario(dedent("""\
        class BrokenTclsh(TclTool):
            def cmdline(self):
                return ["tclsh", "/nonexistent/notcl.tcl"]
        tool = BrokenTclsh(log_fancy=False)
        try:
            with tool as t:
                report("STARTED")
        except ChildProcessEarlyExit:
            report("EARLY_EXIT")
        report("CHILD_RC", tool.proc.returncode)
        report("DONE")
        """), lambda p, line: None, timeout=10)
    assert "SCENARIO: EARLY_EXIT\n" in output
    assert "SCENARIO: CHILD_RC 1\n" in output
    assert "SCENARIO: DONE\n" in output
    assert rc == 0

def test_context_forwards_excepts():
    with pytest.raises(ValueError):
        with Tclsh() as t:
            raise ValueError("test")
