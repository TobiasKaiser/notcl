import tempfile
from contextlib import contextmanager
from pathlib import Path
from enum import Enum
import os

from .message import RawMessage, Message, WrongMessageClass


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

    def recv_raw(self) -> RawMessage:
        assert self.state == self.State.WaitForRecv
        self.log(f"BridgeServer: Opening tcl2py pipe {self.fn_py2tcl} to receive message...")
        with open(self.fn_tcl2py, "rb") as f_in:
            m_recv = RawMessage.from_pipe(f_in)
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