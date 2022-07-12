from .message import Message


class TclHello(Message):
    __slots__ = () # TODO: 
    keys_required = ["patchlevel", "commands", "globals", "nameofexecutable"]

class PyProcedureCall(Message):
    __slots__ = ()
    keys_required = ["command"]

class TclProcedureResult(Message):
    __slots__ = ()
    keys_required = ["err_code", "result", "cmd_idx"]

class PyExit(Message):
    __slots__ = ()
    keys_required = ["quit"]
