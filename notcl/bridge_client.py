from .message import RawMessage, Message, WrongMessageClass
from . import msg_classes as msg

class BridgeClient:
    """This is a dummy client for testing BridgeServer.
    In production, this client is implemented in Tcl."""
    def __init__(self, fn_tcl2py, fn_py2tcl):
        self.fn_tcl2py = fn_tcl2py
        self.fn_py2tcl = fn_py2tcl

    def send(self, msg: Message):
        with open(self.fn_tcl2py, "wb") as f_out:
            msg.to_raw_message().send_to_pipe(f_out)


    def recv(self, permitted_msg_classes):
        """permitted_msg_classes can be either one message class or a list of message classes."""

        with open(self.fn_py2tcl, "rb") as f_in:
            raw_message = RawMessage.from_pipe(f_in)
        return raw_message.to_message(permitted_msg_classes)

    def run(self):
        self.send(msg.TclHello(nameofexecutable="dummy_client"))

        while True:
            m_recv = self.recv([msg.PyProcedureCall, msg.PyExit]) 
            if isinstance(m_recv, msg.PyExit):
                break
            elif isinstance(m_recv, msg.PyProcedureCall):
                result = m_recv.command.upper()
                self.send(msg.TclProcedureResult(result=result, err_code="0"))
            else:
                raise Exception(f"Unexpected message: {m_recv}")
