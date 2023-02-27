import re
from functools import reduce

"""
The Return value of a Tcl command or procedure is basically a string. Without
knowledge about the structure or type of the return value, it is not possible to
convert this string to a meaningful data structure such as a list or dict in Python.

Return values from Tcl are wrapped in *TclRemoteObjRef* objects. Passing a
*TclRemoteObjRef* back to Tcl via *TclToolInterface* method calls causes the
interpreter to use a reference that was maintained within the Tcl tool as
argument, instead of passing a newly created string as argument. While this
should not make a difference *in theory*, some Tcl-based tools rely on
internal representations or object addresses of opaque handles to stay the same.
A *TclRemoteObjRef* can be converted to a string via *str()*.
"""

class TclRemoteObjRef:
    """
    Tcl return values are encapsulated in instances of TclRemoteObjRef.
    Using str(), the string representation of the TclRemoteObjRef can be
    accessed. 
    """

    def __init__(self, tool, cmd_idx:int, value:str, cmd:str):
        self.tool = tool
        self.cmd_idx = cmd_idx
        self.value = value
        self.cmd=cmd

    def __repr__(self):
        return f'Tcl{repr(self.value)}'

    def ref_str(self):
        """
        Returns:
            A Tcl string referencing the corresponding Tcl object in the
            $cmd_results Tcl array, e. g. '$cmd_results(123)'.
        """
        return f"$cmd_results({self.cmd_idx})"

    def __str__(self):
        return self.value

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __getattr__(self, name):
        """
        Similar to TclToolInterface.__getattr__. In addition to methods of
        TclToolInterface, methods returned by this __getattr__ include the
        TclRemoteObjRef as part of the Tcl string that is to be evaluated.

        Exmaple::
        
            v = t.concat("MyObj")
            v.mymethod("arg1", "arg2")

        If TclTool.called_object_pos is 'first', the object name is used as Tcl
        command name: 'MyObj mymethod arg1 arg2'

        If TclTool.called_object_pos is 'second', the method name is the command
        name and the object name comes right after the method name:
        'mymethod MyObj arg1 arg2'

        If TclTool.called_object_pos is 'last', the object name is appended
        at the end of the argument list: 'mymethod arg1 arg2 MyObj'
        """

        return lambda *args, **kwargs: self.proc_call(name, args, kwargs)

    def proc_call(self, name, args, kwargs):
        """
        Wrapper for TclTool.proc_call for using TclRemoteObjRefs in an
        object-oriented way. Internally invoked; do not use directly.
        """
        pos = self.tool.called_object_pos
        if pos == "first":
            args = (name, ) + args
            name = self.ref_str()
        elif pos == "second":
            args = (self, ) + args
        elif pos == "last":
            args = args + (self, )
        else:
            raise ValueError('called_object_pos must be "first", "second" or "last".')
        return self.tool.proc_call(name, args, kwargs)

# TODO: Is there a problem with escape_braces?
def escape_braces(data) -> str:
    return re.sub(r"([{}])", r"\\\1", data)

def encode(obj, nested:bool=False) -> str:
    """
    Encodes Python lists, tuples, dictionaries and simple scalar types in
    Tcl-friendly strings. 

    Returns:
        obj encoded as Tcl string
    """

    if isinstance(obj, (list, tuple)):
        return "{" + " ".join(map(lambda elem: encode(elem, nested=True), obj)) + "}"
    elif isinstance(obj, dict):
        item_list = reduce(lambda a, b: a+b, obj.items())
        return "{" + " ".join(map(lambda elem: encode(elem, nested=True), item_list)) + "}"
    elif isinstance(obj, TclRemoteObjRef) and not nested:
        return obj.ref_str()
    else:
        return "{" + escape_braces(str(obj)) + "}"
