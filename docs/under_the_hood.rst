Under the Hood
==============

The Tcl-based tool is called as subprocess. By running the *notcl.tcl* script on startup, it establishes a connection to its parent Python process and sends some general information using the *TclHello* message. The parent Python process sennds *PyProcedureCall* messages to the Tcl child. The Tcl child runs the requested procedure and sends the return value to the parent process using a *TclProcedureResult* message. Using the *PyExit* message, the Python terminates the Tcl child or finishes execution of *notcl.tcl* without termination, allowing for subsequent interactive Tcl use.

Message passing
---------------

A pair of named pipes is used for message passing between Tcl child and Python parent. Pipe filenames are passed via the environment variables NOTCL_PIPE_TCL2PY and NOTCL_PIPE_PY2TCL.

The Tcl child opens and closes the pipes for every send or receive operation.  
Keeping the pipes open in Tcl leads to problems with Tcl-based tools that do not maintain integrity of user-opened files, e.g. when they use multiple threads or processes. Pipes were chosen instead of Unix domain sockets, as Unix domain sockets are not well-supported in Tcl.

In both directions, messages are lists of key-value pairs. Keys and values are Base64-encoded and separated by newlines. Messages end with EOF. The *class* key specifies the message class. *TclHello* and *TclProcedureResult* are valid message classes from Tcl to Python; *PyProcedureCall* and *PyExit*  are valid message classes from Python to Tcl.