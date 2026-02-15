# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import os
import traceback
import subprocess
import importlib.resources
from typing import Literal, Union, Optional
from abc import ABC, abstractmethod
from pathlib import Path
from contextlib import contextmanager

from . import tclobj, tcl
from . import msg_classes as msg

from .tclobj import TclRemoteObjRef
from .bridge_server import BridgeServer, ChildProcessEarlyExit

class ANSITerm:
    FgBrightYellow = "\x1b[93m"
    BgRed = "\x1b[41m"
    BgGreen = "\x1b[42m"
    Reset = "\x1b[0m"

class TclError(Exception):
    """
    Exception raised when a Tcl command fails.

    When a Tcl command returns an error (non-zero error code), NoTcl raises
    a TclError with the Tcl error message. The TclTool remains usable after
    catching the exception.

    Attributes:
        text: The Tcl error message.

    Example::

        from notcl import TclError

        with Tclsh() as t:
            try:
                t.expr("invalid syntax")
            except TclError as e:
                print(f"Tcl error: {e}")
            # Tool is still usable
            result = t.expr(1, "+", 1)
    """
    def __init__(self, text: str):
        super().__init__(text)
        self.text = text

    def __str__(self):
        return self.text


class TclTool(ABC):
    """
    Base class for wrapping Tcl-based tools as Python interfaces.

    TclTool spawns a Tcl tool as a subprocess and communicates with it via
    named pipes. Subclasses must implement the ``cmdline()`` method to specify
    how to invoke the tool.

    Example::

        from notcl import TclTool

        class Tclsh(TclTool):
            def cmdline(self):
                return ["tclsh", self.script_name()]

        with Tclsh() as t:
            result = t.expr(3, "*", 5)
            print(result)  # 15

    The tool is used as a context manager. On entry, the subprocess is spawned
    and a communication channel is established. On exit, the tool is terminated
    (unless ``interact=True``).

    All Tcl commands and procedures become callable as methods on the
    TclToolInterface object yielded by the context manager. Return values are
    wrapped in TclRemoteObjRef objects that preserve opaque handles when passed
    back to Tcl.
    """

    called_object_pos = "second"
    """
    Used in TclRemoteObjRef.proc_call, specifying the invokation style for
    TclRemoteObjRef methods. Can be overwritten in subclasses.
    Must be 'first', 'second' oder 'last' (see TclRemoteObjRef.proc_call).
    """

    def __init__(self, cwd:Optional[Union[Path, str]]=None, interact:bool=False,
            log_commands:bool=True, log_retvals:bool=False, log_fancy:bool=True,
            debug_tcl:bool=False, debug_py:bool=False, abort_on_error:bool=True):
        """
        Initialize the TclTool.

        Args:
            cwd: Working directory for the Tcl tool subprocess. Defaults to the
                current working directory.
            interact: If True, keep the Tcl tool open for interactive use after
                the with block exits. The Python script waits for manual
                termination. Default: False.
            log_commands: Print all Tcl commands sent to the tool to stdout.
                Default: True.
            log_retvals: Print all return values received from Tcl to stdout.
                Default: False.
            log_fancy: Use ANSI color codes in log output. Default: True.
            debug_tcl: Enable detailed debug output from the Tcl side. Default: False.
            debug_py: Enable detailed debug output from the Python side. Default: False.
            abort_on_error: Terminate the child process when a Tcl error occurs,
                even if interact=True. Default: True.
        """

        self.interact = interact
        self.log_commands = log_commands
        self.log_retvals = log_retvals
        self.log_fancy = log_fancy
        self.debug_tcl=debug_tcl
        self.debug_py=debug_py
        self.abort_on_error = abort_on_error
        self._script_name = None
        self.cm = None
        
        if not cwd:
            self.cwd = Path.cwd()
        else:
            self.cwd = Path(cwd)

    @abstractmethod
    def cmdline(self) -> list[str]:
        """
        Return the command line for invoking the Tcl tool.

        Subclasses must implement this method to specify how to start the tool.
        The returned list is passed to subprocess.Popen.

        Returns:
            List of strings where the first element is the executable name or path,
            and subsequent elements are command line arguments. The tool must be
            configured to execute the script returned by self.script_name() at
            startup.

        Example::

            def cmdline(self):
                return ["tclsh", self.script_name()]
        """
        pass

    def script_name(self) -> str:
        """
        Return the path to the NoTcl communication script.

        This method should be called from cmdline() to get the path to the
        notcl.tcl script that the tool must execute at startup.

        Returns:
            Path to the notcl.tcl script when called during cmdline() execution.
            Returns a placeholder string at other times.

        Note:
            The path is only valid while cmdline() is being executed. Do not
            cache or store this value.
        """
        # This used to be a call to pkg_resources. After migration to
        # importlib.resources, this now is only a wrapper to get a value
        # passed from contextmanager(self), which obtains it as context
        # from importlib.resources.as_file.
        if self._script_name==None:
            return "<placeholder for notcl.tcl>"
        else:
            return self._script_name

    def env(self) -> dict[str, str]:
        """
        Returns:
            Modified environment for child process.
        """
        env = os.environ.copy()
        env["NOTCL_PIPE_TCL2PY"]=self.bs.fn_tcl2py
        env["NOTCL_PIPE_PY2TCL"]=self.bs.fn_py2tcl
        env["NOTCL_PIPE_SENTINEL"]=self.bs.fn_sentinel
        env["NOTCL_DEBUG_TCL"]=("1" if self.debug_tcl else "0")
        return env

    def debug_log(self, message:str):
        """
        Prints debug message, if debug output is enabled by debug_py flag.
        """
        if self.debug_py:
            print(f"[notcl] Python: {message}")


    @contextmanager
    def contextmanager(self):
        """
        Coroutine for invoking the Tcl tool on entry of the with block and
        waiting for the Tcl tool to finish when leaving the with block. It is
        invoked and managed internally by __enter__ and __exit__;
        not normally used externally.
        """

        child_exited_early = False

        with BridgeServer(custom_log_func=self.debug_log) as self.bs,\
            importlib.resources.as_file(importlib.resources.files(tcl).joinpath("notcl.tcl")) as script_name:

            try:
                self._script_name = script_name
                cmdline = self.cmdline()
            finally:
                # Clear self._script_name to make sure it never contains an invalid
                # invalid path (after leaving the script_name context here):
                self._script_name = None

            env = self.env()
            cwd = self.cwd

            self.proc = subprocess.Popen(cmdline, cwd=cwd, env=env)

            # Open sentinel read end early (before TclHello) so the Tcl
            # side's blocking WRONLY open on the sentinel FIFO can proceed.
            # O_NONBLOCK means this open returns immediately even without
            # a writer; the sentinel fd will show premature EOF until the
            # child connects, which recv_raw handles via FIONREAD.
            self.bs.open_sentinel()

            quit = not self.interact

            try:
                self.hello = self.bs.recv(msg.TclHello)
                self.debug_log(f"Received TclHello: {self.hello}")

                try:
                    yield TclToolInterface(self)
                except ChildProcessEarlyExit:
                    child_exited_early = True
                    raise
                except Exception:
                    self.debug_log("Caught exception in TclTool context.")
                    if self.abort_on_error:
                        quit = True
                    else:
                        s = traceback.format_exc()
                        self.log("error",
                            "Following exception is held back and will be raised "
                            f"once the Tcl child process exists:\n{s}")
                    raise
            except ChildProcessEarlyExit:
                child_exited_early = True
                raise
            finally:
                if not child_exited_early:
                    self.debug_log("Sending PyExit")

                    if not quit:
                        self.log("info", "Python control finished. Please exit Tcl tool to continue Python script.")
                    try:
                        self.bs.send(msg.PyExit(quit='1' if quit else '0'))
                    except ChildProcessEarlyExit:
                        child_exited_early = True

                self.debug_log("TclTool context finished, waiting for child process to terminate.")
                rc = self.proc.wait()

                if child_exited_early:
                    self.debug_log(f"Child exited early with return code {rc}.")
                elif rc == 0:
                    self.debug_log(f"Child process terminated with return code {rc}.")
                else:
                    self.debug_log(f"Child process terminated with abnormal return code {rc}.")
                    raise subprocess.CalledProcessError(rc, cmdline)

    def __enter__(self):
        assert self.cm == None
        self.cm = self.contextmanager()
        return self.cm.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        assert self.cm
        cm = self.cm
        self.cm = None
        return cm.__exit__(exc_type, exc_value, traceback)

    def proc_call(self, cmd:str, args:list, kwargs:dict):
        """
        Calls a procedure or command within Tcl. This method is invoked
        internally by calling a TclToolInterface method; do not use directly.

        Args:
            cmd: name of the Tcl procedure or command.
            args: list of positional arguments.
            kwargs: dictionary of keyword arguments.
        """

        # Reason why we have args and kwargs here instead of *args and **kwards: This
        # way we can support -self or -cmd als names Tcl command arguments.

        full_cmd = [cmd]
        for k, v in kwargs.items():
            if type(v)==bool:
                if v:
                    full_cmd.append("-"+k)
            else:
                full_cmd.append("-"+k)
                full_cmd.append(tclobj.encode(v))

        for arg in args:
            full_cmd.append(tclobj.encode(arg))

        return self.eval(" ".join(full_cmd))

    def log(self, log_type:Literal["command", "info", "retval", "error"], data:str):
        """
        log prints log messages for every Tcl command invokation and every
        received return value or error. It is enabled/disabled by the logs
        argument passed to __init__.
        """
        assert log_type in ("command", "retval", "error", "info")
        if log_type == "command":
            self.debug_log(f"Running command: {data}")
            if not self.log_commands:
                return
            log_symbol = "Cmd:"
        elif log_type == "retval":
            self.debug_log(f"Return value: {data}")
            if not self.log_retvals:
                return
            log_symbol = "Result:"
        elif log_type == "error":
            self.debug_log(f"Received error as return value: {data}")
            log_symbol = "Error:"
        elif log_type == "info":
            log_symbol = "Info:"

        style_notcl = ""
        style_reset = ""
        style_symbol = ""

        if self.log_fancy:
            style_notcl = ANSITerm.FgBrightYellow
            style_reset = ANSITerm.Reset
            if log_type=="error":
                style_symbol = ANSITerm.BgRed
            elif log_type=="info":
                style_symbol = ANSITerm.BgGreen

        print(f"{style_notcl}[notcl]{style_reset} {style_symbol}{log_symbol}{style_reset} {data}")

    def eval(self, cmd: str) -> TclRemoteObjRef:
        """
        Evaluate a Tcl command string directly.

        This is a low-level method. Prefer using the method call syntax on
        TclToolInterface (e.g., t.expr(3, "*", 5)) for most use cases.

        Args:
            cmd: Tcl command string to evaluate.

        Returns:
            TclRemoteObjRef wrapping the return value.

        Raises:
            TclError: If the Tcl command fails.
        """
        self.log("command", cmd)
        self.bs.send(msg.PyProcedureCall(command=cmd))
        r_msg = self.bs.recv(msg.TclProcedureResult)
        cmd_idx = int(r_msg.cmd_idx)
        err_code = int(r_msg.err_code)

        if err_code:
            self.log("error", f"{r_msg.result}")
            raise TclError(r_msg.result)
        else:
            self.log("retval", r_msg.result)
            return TclRemoteObjRef(self, cmd_idx, r_msg.result, cmd)


class TclToolInterface:
    """
    Interface for calling Tcl commands as Python methods.

    TclToolInterface is yielded when entering a TclTool context. All Tcl
    commands and procedures become callable as methods on this object.

    Method calls are automatically translated to Tcl command invocations, with
    Python arguments converted to Tcl-friendly strings. Return values are
    wrapped in TclRemoteObjRef objects.

    Example::

        with Tclsh() as t:
            # t is a TclToolInterface object
            result = t.expr(3, "*", 5)  # Calls Tcl command: expr {3} {*} {5}
            print(result)  # 15
    """
    def __init__(self, tcl_tool:TclTool):
        self.tcl_tool = tcl_tool

    def __getattr__(self, name):
        """
        Return a callable that invokes the Tcl command with the given name.

        Any attribute access becomes a method call to the corresponding Tcl
        command or procedure. Arguments are automatically converted using
        tclobj.encode().

        Args:
            name: Name of the Tcl command to invoke.

        Returns:
            A callable that accepts ``*args`` and ``**kwargs``, converts them to Tcl
            syntax, and returns a TclRemoteObjRef.

        Example::

            result = t.expr(3, "*", 5)  # Invokes: expr {3} {*} {5}
            items = t.lreverse([1, 2, 3])  # Invokes: lreverse {1 2 3}
        """
        return lambda *args, **kwargs: self.tcl_tool.proc_call(name, args, kwargs)

    def __call__(self, cmd: str) -> TclRemoteObjRef:
        """
        Evaluate a raw Tcl command string.

        Calling the TclToolInterface object directly allows evaluation of
        arbitrary Tcl strings without argument conversion.

        Args:
            cmd: Tcl command string to evaluate.

        Returns:
            TclRemoteObjRef wrapping the return value.

        Raises:
            TclError: If the Tcl command fails.

        Example::

            result = t("expr 3 * 5")  # Direct string evaluation
            result = t.expr(3, "*", 5)  # Equivalent method call
        """
        return self.tcl_tool.eval(cmd)
