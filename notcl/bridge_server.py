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

from .message import RawMessage, Message, WrongMessageClass


class ChildProcessEarlyExit(Exception):
    """
    Raised when the Tcl child process terminates unexpectedly (before the
    TclTool context exits normally). Detected via a sentinel named pipe that
    becomes readable (EOF) when the child process dies.
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
        if custom_log_func:
            self.log = custom_log_func

    def open_sentinel(self):
        """Open the read end of the sentinel pipe. Call this after the child
        process has opened the write end (i.e. after receiving TclHello)."""
        self.sentinel_fd = os.open(self.fn_sentinel, os.O_RDONLY | os.O_NONBLOCK)

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
                self.log("BridgeServer: connection closed.")
                self.state = self.State.NotListening

    def recv_raw(self) -> RawMessage:
        assert self.state == self.State.WaitForRecv
        self.log(f"BridgeServer: Opening tcl2py pipe {self.fn_tcl2py} to receive message...")

        # Open non-blocking so we can monitor the sentinel fd for child death
        # while waiting for the Tcl side to connect and write.
        tcl2py_fd = os.open(self.fn_tcl2py, os.O_RDONLY | os.O_NONBLOCK)
        try:
            while True:
                rdready, _, _ = select.select([tcl2py_fd, self.sentinel_fd], [], [])

                if self.sentinel_fd in rdready:
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
                    # else: no writer yet (premature EOF), continue waiting
        finally:
            if tcl2py_fd >= 0:
                os.close(tcl2py_fd)

        self.log(f"BridgeServer: tcl2py pipe {self.fn_tcl2py} closed.")
        self.state = self.State.WaitForSend
        return m_recv

    def send_raw(self, send_data: RawMessage):
        assert self.state == self.State.WaitForSend
        self.log(f"BridgeServer: Opening py2tcl pipe {self.fn_py2tcl} to send message...")

        # Open non-blocking so we can monitor the sentinel for child death
        # while waiting for the Tcl side to open its read end.
        # O_WRONLY | O_NONBLOCK on a FIFO raises ENXIO when no reader is
        # connected, so we retry in a loop, checking the sentinel between
        # attempts via select with a short timeout.
        while True:
            rdready, _, _ = select.select([self.sentinel_fd], [], [], 0)
            if rdready:
                raise ChildProcessEarlyExit()
            try:
                py2tcl_fd = os.open(self.fn_py2tcl, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as e:
                if e.errno == errno.ENXIO:
                    # No reader yet, wait for sentinel or timeout and retry
                    rdready, _, _ = select.select([self.sentinel_fd], [], [], 0.01)
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
