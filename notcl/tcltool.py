import os
import subprocess
import pkg_resources
import signal
from typing import Literal, Union, Optional
from abc import ABC, abstractmethod
from pathlib import Path
from contextlib import contextmanager

from . import tclobj
from . import msg_classes as msg

from .tclobj import TclRemoteObjRef
from .bridge_server import BridgeServer

class TclError(Exception):
    """
    Errors in Tcl are forwarded to Python and raised in the form of a TclError
    exception. TclErrors can be caught and handled in Python. The corresponding
    TclTool remains usable.
    """
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def __str__(self):
        return self.text

class ChildProcessExited(Exception):
    """
    This exception is raised on abnormal / early termination of the Tcl child
    process through TclTool._sigchld_handler. It interrupts the
    current TclTool context. It is caught in TclTool.contextmanager.
    Typically, TclTool.contextmanager will then raise a subprocess.CalledProcessError
    based on the child's return code.
    """
    pass


class TclTool(ABC):
    called_object_pos = "second"
    """
    Used in TclRemoteObjRef.proc_call, specifying the invokation style for
    TclRemoteObjRef methods. Can be overwritten in subclasses.
    Must be 'first', 'second' oder 'last' (see TclRemoteObjRef.proc_call). 
    """ 

    def __init__(self, cwd:Optional[Union[Path, str]]=None, interact:bool=False,
            log_commands:Literal[False, 'fancy', 'plain']=False,
            debug_tcl:bool=False, debug_py:bool=False):
        """
        Args:
            cwd: Directory in which to Tcl-based tool is run.
            interact: If set to True, the Tcl-based tool will not be terminated
                at the end of the with block. Instead, the Tcl tool remains open
                for the user to interact with. In this case, the Python script
                will wait for the user to close the tool manually before continuing.
            log_commands: When set to 'plain' or 'fancy', every string sent to the
                Tcl tool for evaluation and every resulting return value or error
                will be printed to stdout. 'fancy' adds ANSI controls sequences
                for colorful output.
            debug_tcl: Enable detailed debug output by the Tcl script running in
                the Tcl tool.
            debug_py: Enable detailed debug output for Python side.
        """
        
        if not log_commands in (False, "fancy", "plain"):
            raise TypeError("log_commands must be False, 'fancy' or 'plain'.")
        
        self.interact = interact
        self.log_commands = log_commands
        self.debug_tcl=debug_tcl
        self.debug_py=debug_py

        self.cm = None
        
        if not cwd:
            self.cwd = Path.cwd()
        else:
            self.cwd = Path(cwd)

    @abstractmethod
    def cmdline(self) -> list[str]:
        """
        Returns:
            A list of strings that is passed to subprocess.Popen for invoking
            the Tcl tool. The first list element is the program name or full path
            to the executable. The subsequent list of arguments should be set
            in such a way that the Tcl script returned by self.script_name() is
            executed at startup of the invoked Tcl tool.
        """ 
        pass

    def script_name(self) -> str:
        """
        Returns:
            Filename of notcl.tcl file
        """
        return pkg_resources.resource_filename(__name__, "notcl.tcl")


    def env(self) -> dict[str, str]:
        """
        Returns:
            Modified environment for child process.
        """
        env = os.environ.copy()
        env["NOTCL_PIPE_TCL2PY"]=self.bs.fn_tcl2py
        env["NOTCL_PIPE_PY2TCL"]=self.bs.fn_py2tcl
        env["NOTCL_DEBUG_TCL"]=("1" if self.debug_tcl else "0")
        return env

    def debug_log(self, message:str):
        """
        Prints debug message, if debug output is enabled by debug_py flag. 
        """
        if self.debug_py:
            print(f"[notcl] Python: {message}")

    def _sigchld_handler(self, sig, frame):
        """
        Called when child process exists, vis SIGHCLD Unix signal.
        This will typically interrupt the open() call in BridgeServer.recv_raw.
        """
        self.debug_log("Received SIGCHLD (child process terminated)")
        raise ChildProcessExited()
            

    @contextmanager
    def contextmanager(self):
        """
        Coroutine for invoking the Tcl tool on entry of the with block and
        waiting for the Tcl tool to finish when leaving the with block. It is
        invoked and managed internally by __enter__ and __exit__;
        not normally used externally.
        """
        cmdline = self.cmdline()
        
        with BridgeServer(custom_log_func=self.debug_log) as self.bs:
            
            env = self.env()
            cwd = self.cwd
            
            signal.signal(signal.SIGCHLD, self._sigchld_handler)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            
            self.proc = subprocess.Popen(cmdline, cwd=cwd, env=env)
            
            clean_exit = True

            try:
                self.hello=self.bs.recv(msg.TclHello)
                self.debug_log(f"Received TclHello: {self.hello}")
                try:
                    yield TclToolInterface(self)
                except ChildProcessExited:
                    clean_exit = False
                finally:
                    if clean_exit:
                        self.debug_log("Sending PyExit")
                        quit = "0" if self.interact else "1"
                        self.bs.send(msg.PyExit(quit=quit))
            except:
                self.debug_log("Caught exception in TclTool context.")
                # Exception info could be extracted here from sys.exc_info (?)
                raise
            finally:
                # TODO: There is at least one unhandled race condition here:
                # What if we receive SIGCHLD before the signal handler is disabled?

                signal.signal(signal.SIGCHLD, signal.SIG_IGN)
                signal.signal(signal.SIGINT, signal.SIG_DFL)
                
                self.debug_log("TclTool context finished, waiting for child process to terminate.")
                rc = self.proc.wait()

                if rc==0:
                    self.debug_log("Child process terminated with return code {rc}.")
                else:
                    self.debug_log("Child process terminated with abnormal return code {rc}.")
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

    def log_command(self, log_type:Literal["command", "result", "error"], data:str):
        """
        log_command prints log messages for every Tcl command invokation and every
        received return value or error. It is enabled/disabled by the log_commands
        argument passed to __init__.
        """
        assert log_type in ("command", "result", "error")
        if log_type == "command":
            self.debug_log(f"Running command: {data}")
            log_symbol = "-->"
        elif log_type == "result":
            self.debug_log(f"Received return value: {data}")
            log_symbol = "<--"
        elif log_type == "error":
            self.debug_log(f"Received error as return value: {data}")
            log_symbol = "<!!"

        if self.log_commands=='fancy':
            style_notcl = "\x1b[1;46m"
            if log_type=="error":
                style_symbol = "\x1b[1;41m"
            else:
                style_symbol = "\x1b[1;32m"
            style_reset = "\x1b[0m"
        elif self.log_commands=='plain':
            style_notcl = ""
            style_reset = ""
            style_symbol = ""
        else:
            assert not self.log_commands
            return
        
        print(f"{style_notcl}[notcl]{style_reset} {style_symbol}{log_symbol}{style_reset} {data}{style_reset}")


    def eval(self, cmd: str) -> TclRemoteObjRef:
        """
        Low-level method that passes a string to Tcl for evaluation.
        """
        self.log_command("command", cmd)
        self.bs.send(msg.PyProcedureCall(command=cmd))
        r_msg = self.bs.recv(msg.TclProcedureResult)
        cmd_idx = int(r_msg.cmd_idx)
        err_code = int(r_msg.err_code)
        
        if err_code:
            self.log_command("error", cmd)
            raise TclError(r_msg.result)
        else:
            self.log_command("result", r_msg.result)
            return TclRemoteObjRef(self, cmd_idx, r_msg.result, cmd)
        

class TclToolInterface:
    """
    Entering a with block using a TclTool yields a TclToolInterface.

    Example::

        with MyTclTool() as t:
            # t is a TclToolInterface object.
            pass
    """
    def __init__(self, tcl_tool:TclTool):
        self.tcl_tool = tcl_tool

    def __getattr__(self, name):
        """
        For every unknown attribute, a method is returned that that calls the 
        Tcl command or procedure of corresponding name.

        Example use for a TclToolInterface t, in which the method returned by
        __getattr__ is immediately called, returning a TclRemoteObjRef::

            v = t.expr(3, "*", 5)
        """
        return lambda *args, **kwargs: self.tcl_tool.proc_call(name, args, kwargs)

    def __call__(self, cmd: str) -> TclRemoteObjRef:
        """
        Calling TclToolInterface allows low-level evaluation of a strings without
        using the higher-level method calls.

        Example use for a TclToolInterface t::

            v = t("expr 3 * 5")
        """
        return self.tcl_tool.eval(cmd)
