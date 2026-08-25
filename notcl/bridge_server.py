# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import tempfile
from contextlib import contextmanager, closing
from pathlib import Path
from enum import Enum
import os
import errno
import fcntl
import struct
import select
import termios

from .message import RawMessage, Message


class ChildProcessEarlyExit(Exception):
    """
    Exception raised when the Tcl subprocess terminates unexpectedly.

    This exception is raised when the Tcl child process exits before the
    TclTool context manager exits normally. This can happen if:

    - The Tcl process crashes
    - The Tcl process calls exit explicitly
    - The Tcl process is killed by a signal

    NoTcl detects early termination via a sentinel named pipe that becomes
    readable (EOF) when the child process dies.

    Example::

        from notcl import ChildProcessEarlyExit

        try:
            with Tclsh() as t:
                t.exit(0)  # Tcl process terminates
                t.expr(1, "+", 1)  # Never reached
        except ChildProcessEarlyExit:
            print("Tcl process exited early")
    """
    pass


class BridgeServer:
    class State(Enum):
        NotListening = 0
        WaitForRecv = 1
        WaitForSend = 2

    def log(self, message):
        """Replace this method with something else to change the log mechanism"""
        print(f"[BridgeServer] {message}")

    def __init__(self, custom_log_func=None):
        self.cm = None
        self.state = self.State.NotListening
        self.sentinel_fd = None
        self.pidfd = None
        if custom_log_func:
            self.log = custom_log_func

    def open_sentinel(self):
        """Open the read end of the sentinel pipe. Must be called before
        recv(TclHello) so the Tcl side's blocking WRONLY open can proceed."""
        self.sentinel_fd = os.open(self.fn_sentinel, os.O_RDONLY | os.O_NONBLOCK)

    def watch_child(self, pid):
        """
        Additionally monitors the child process itself via a pidfd, which
        becomes readable when the process exits. The sentinel pipe only
        reports the child's death if the child has opened it, which a child
        that fails before running notcl.tcl (e.g. due to invalid command
        line args) never does. Without pidfd support (non-Linux, Linux
        before 5.3), only the sentinel is monitored.
        """
        try:
            self.pidfd = os.pidfd_open(pid)
        except (AttributeError, OSError) as e:
            self.log(f"BridgeServer: pidfd not available ({e!r}), monitoring sentinel only.")

    def _exit_fds(self):
        """File descriptors that become readable when the child exits."""
        fds = [self.sentinel_fd]
        if self.pidfd is not None:
            fds.append(self.pidfd)
        return fds

    def child_exited(self) -> bool:
        """
        True if the child process has exited, i.e. one of the exit fds is
        readable. Before the child connects to the sentinel, the sentinel
        fd is not reported readable (no writer has been connected yet), so
        this can be called any time after open_sentinel().
        """
        rdready, _, _ = select.select(self._exit_fds(), [], [], 0)
        return bool(rdready)

    @staticmethod
    def _bytes_available(fd):
        """Return the number of bytes available to read on fd (FIONREAD)."""
        buf = fcntl.ioctl(fd, termios.FIONREAD, b'\x00\x00\x00\x00')
        return struct.unpack('i', buf)[0]

    @contextmanager
    def contextmanager(self):
        assert self.state == self.State.NotListening
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.fn_tcl2py = str(Path(tmp_dir) / "tcl2py")
            self.fn_py2tcl = str(Path(tmp_dir) / "py2tcl")
            self.fn_sentinel = str(Path(tmp_dir) / "sentinel")
            os.mkfifo(self.fn_tcl2py)
            os.mkfifo(self.fn_py2tcl)
            os.mkfifo(self.fn_sentinel)
            self.state = self.state.WaitForRecv
            try:
                yield self
            finally:
                if self.sentinel_fd is not None:
                    os.close(self.sentinel_fd)
                if self.pidfd is not None:
                    os.close(self.pidfd)
                self.log("BridgeServer: connection closed.")
                self.state = self.State.NotListening

    def recv_raw(self) -> RawMessage:
        assert self.state == self.State.WaitForRecv
        self.log(f"BridgeServer: Opening tcl2py pipe {self.fn_tcl2py} to receive message...")

        # Open non-blocking so we can monitor the exit fds for child death
        # while waiting for the Tcl side to connect and write.
        tcl2py_fd = os.open(self.fn_tcl2py, os.O_RDONLY | os.O_NONBLOCK)
        try:
            while True:
                rdready, _, _ = select.select([tcl2py_fd] + self._exit_fds(), [], [])

                if any(fd in rdready for fd in self._exit_fds()):
                    raise ChildProcessEarlyExit()

                if tcl2py_fd in rdready:
                    # select says readable. This could be:
                    # - No writer connected (premature EOF): FIONREAD == 0
                    # - Writer connected and data available: FIONREAD > 0
                    # We use FIONREAD to distinguish without consuming data.
                    if self._bytes_available(tcl2py_fd) > 0:
                        # Data available. Switch to blocking mode and read
                        # the full message (from_pipe reads until EOF).
                        flags = fcntl.fcntl(tcl2py_fd, fcntl.F_GETFL)
                        fcntl.fcntl(tcl2py_fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
                        with closing(os.fdopen(tcl2py_fd, 'rb')) as f_in:
                            m_recv = RawMessage.from_pipe(f_in)
                        tcl2py_fd = -1  # fdopen took ownership
                        break
                    else:
                        # No writer yet (premature EOF). Sleep briefly via
                        # select on the exit fds to avoid busy-looping while
                        # still detecting child death promptly.
                        select.select(self._exit_fds(), [], [], 0.01)
        finally:
            if tcl2py_fd >= 0:
                os.close(tcl2py_fd)

        self.log(f"BridgeServer: tcl2py pipe {self.fn_tcl2py} closed.")
        self.state = self.State.WaitForSend
        return m_recv

    def send_raw(self, send_data: RawMessage):
        assert self.state == self.State.WaitForSend
        self.log(f"BridgeServer: Opening py2tcl pipe {self.fn_py2tcl} to send message...")

        # Open non-blocking so we can monitor the exit fds for child death
        # while waiting for the Tcl side to open its read end.
        # O_WRONLY | O_NONBLOCK on a FIFO raises ENXIO when no reader is
        # connected, so we retry in a loop, checking the exit fds between
        # attempts via select with a short timeout.
        while True:
            rdready, _, _ = select.select(self._exit_fds(), [], [], 0)
            if rdready:
                raise ChildProcessEarlyExit()
            try:
                py2tcl_fd = os.open(self.fn_py2tcl, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as e:
                if e.errno == errno.ENXIO:
                    # No reader yet, wait for exit fds or timeout and retry
                    rdready, _, _ = select.select(self._exit_fds(), [], [], 0.01)
                    if rdready:
                        raise ChildProcessEarlyExit()
                    continue
                raise
            break

        try:
            # Clear O_NONBLOCK for the actual write
            flags = fcntl.fcntl(py2tcl_fd, fcntl.F_GETFL)
            fcntl.fcntl(py2tcl_fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
            with closing(os.fdopen(py2tcl_fd, 'wb')) as f_out:
                send_data.send_to_pipe(f_out)
            py2tcl_fd = -1  # fdopen took ownership
        except BrokenPipeError:
            raise ChildProcessEarlyExit()
        finally:
            if py2tcl_fd >= 0:
                os.close(py2tcl_fd)

        self.log(f"BridgeServer: py2tcl pipe {self.fn_py2tcl} closed.")
        self.state = self.State.WaitForRecv

    def recv(self, permitted_msg_classes) -> Message:
        """permitted_msg_classes can be either one message class or a list of message classes."""
        return self.recv_raw().to_message(permitted_msg_classes)

    def send(self, message: Message):
        raw_msg = message.to_raw_message()
        self.send_raw(raw_msg)

    def __enter__(self):
        assert self.cm == None
        self.cm = self.contextmanager()
        return self.cm.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        assert self.cm
        cm = self.cm
        self.cm = None
        return cm.__exit__(exc_type, exc_value, traceback)
