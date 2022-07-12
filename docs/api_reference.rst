API Reference
=============

TclTool class
-------------

A subclass of TclTool needs to be defined before it can be used. Example::
   
   class Tclsh(TclTool):
        def cmdline(self):
            return ["tclsh", self.script_name()]

.. autoclass:: notcl.TclTool
   :members:

   .. automethod:: __init__

.. autoclass:: notcl.tcltool.TclToolInterface
   :members:

   .. automethod:: __getattr__
   .. automethod:: __call__


Return values and errors
------------------------

.. autoclass:: notcl.tclobj.TclRemoteObjRef
   :members:

.. autoclass:: notcl.TclError
   :members:
