Under the Hood
==============

TODO

RPC-like

Message passing
---------------

Opening / closing named Unix pipes

Why pipes instead of not Unix domain sockets? Unix domain sockets are not supported out-of-the-box in Tcl.

Why are the pipes repeatedly opened and closed, not held open?


Protocol
--------

Message format and message types...

Tcl... originate from Tcl.

Py... originate form Python.

- tcl -> python: TclHello
- loop:
  
  - python -> tcl: PyProcedureCall
  - tcl -> python: TclProcedureResult

- python -> tcl: PyExit
