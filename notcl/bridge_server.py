# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import tempfile
from contextlib import contextmanager, closing
from pathlib import Path
from enum import Enum
import os
import fcntl
import select
import signal
import fcntl
from .message import RawMessage, Message, WrongMessageClass

class ChildEarlyExit(Exception):
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
        if custom_log_func:
            self.log = custom_log_func

    @contextmanager
    def contextmanager(self):
        assert self.state == self.State.NotListening
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.fn_tcl2py = str(Path(tmp_dir) / "tcl2py")
            self.fn_py2tcl = str(Path(tmp_dir) / "py2tcl")
            os.mkfifo(self.fn_tcl2py)
            os.mkfifo(self.fn_py2tcl)
            self.state = self.state.WaitForRecv
            try:
                yield self
            finally:
                self.log("BridgeServer: connection closed.")
                self.state = self.State.NotListening

    def recv_raw(self, watch_child_for_termination: "subprocess.Popen") -> RawMessage:
        assert self.state == self.State.WaitForRecv
        self.log(f"BridgeServer: Opening tcl2py pipe {self.fn_tcl2py} to receive message...")

        # O_NONBLOCK makes sure the open does not block even though other side is not connected yet.
        tcl2py_fd = os.open(self.fn_tcl2py, os.O_RDONLY | os.O_NONBLOCK)

        sig_pipe_r, sig_pipe_w = os.pipe()
        flags = fcntl.fcntl(sig_pipe_w, fcntl.F_GETFL)
        flags |=  os.O_NONBLOCK
        fcntl.fcntl(sig_pipe_w, fcntl.F_SETFL, flags)
        old_wakeup_fd = signal.set_wakeup_fd(sig_pipe_w)

        signal.signal(signal.SIGCHLD, lambda a, b: None)
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        
        try:
            with closing(os.fdopen(tcl2py_fd, 'rb')) as f_in:
                while True:
                    if watch_child_for_termination != None and watch_child_for_termination.poll() != None:
                        self.log(f"BridgeServer: Child {watch_child_for_termination} exited early.")
                        raise ChildEarlyExit()
                    rdready, _, _, = select.select([tcl2py_fd, sig_pipe_r], [], [])
                    if tcl2py_fd in rdready:
                        m_recv = RawMessage.from_pipe(f_in)
                        break
        finally:
            signal.signal(signal.SIGCHLD, signal.SIG_DFL)
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        self.log(f"BridgeServer: tcl2py pipe {self.fn_py2tcl} closed.")

        self.state = self.State.WaitForSend
        return m_recv

    def send_raw(self, send_data: RawMessage):
        assert self.state == self.State.WaitForSend
        self.log(f"BridgeServer: Opening py2tcl pipe {self.fn_py2tcl} to send message...")
        with open(self.fn_py2tcl, "wb") as f_out:
            send_data.send_to_pipe(f_out)
        self.log(f"BridgeServer: py2tcl pipe {self.fn_py2tcl} closed.")
            
        self.state = self.State.WaitForRecv

    def recv(self, permitted_msg_classes, watch_child_for_termination: "subprocess.Popen") -> Message:
        """permitted_msg_classes can be either one message class or a list of message classes."""
        return self.recv_raw(watch_child_for_termination).to_message(permitted_msg_classes)

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