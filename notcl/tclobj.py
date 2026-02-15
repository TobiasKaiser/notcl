# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

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
    Wrapper for Tcl command return values that preserves opaque handles.

    All Tcl command return values are wrapped in TclRemoteObjRef objects.
    When passed back to Tcl, NoTcl uses a reference to the original Tcl object
    rather than its string representation, preserving the internal representation
    and memory address of opaque handles.

    TclRemoteObjRef supports conversion to Python types via str(), int(), and
    float(). For object-oriented Tcl APIs, methods can be called on the
    TclRemoteObjRef (see __getattr__).

    Example::

        result = t.expr(3, "*", 5)
        print(str(result))  # "15"
        print(int(result))  # 15

        handle = t.create_object()
        t.modify_object(handle)  # Uses Tcl reference, not string
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
        Get the Tcl reference string for this object.

        Returns:
            A Tcl variable reference string (e.g., "$cmd_results(123)") that
            can be used in raw Tcl command strings to reference this object.

        Example::

            handle = t.create_object()
            t(f"puts {handle.ref_str()}")  # Explicitly use Tcl reference
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
        Enable object-oriented method calls on Tcl objects.

        Similar to TclToolInterface.__getattr__, but includes this TclRemoteObjRef
        in the generated Tcl command. The position is controlled by
        TclTool.called_object_pos.

        Args:
            name: Method name to call.

        Returns:
            A callable that invokes the Tcl command with this object reference.

        Example::

            obj = t.create_object()
            obj.set_property("value")  # Method call on the object

        The object position in the generated Tcl command depends on
        TclTool.called_object_pos:

        - 'first': object is command name (e.g., "$obj method arg1 arg2")
        - 'second': object follows method (e.g., "method $obj arg1 arg2")
        - 'last': object is last argument (e.g., "method arg1 arg2 $obj")
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
