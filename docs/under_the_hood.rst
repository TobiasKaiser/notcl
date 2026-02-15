Under the Hood
==============

NoTcl uses a subprocess-based architecture with named pipe (FIFO) communication. This section describes the implementation details.

Process architecture
--------------------

When a :class:`~notcl.TclTool` context is entered, NoTcl spawns the Tcl tool as a subprocess and establishes bidirectional communication via named pipes. The tool executes the ``notcl.tcl`` script at startup, which implements the Tcl side of the communication protocol.

The lifecycle is:

1. Python creates three named pipes (FIFOs) in a temporary directory
2. Python spawns the Tcl tool subprocess with ``notcl.tcl`` as the startup script
3. Tcl opens the sentinel pipe (to signal liveness) and sends a ``TclHello`` message
4. Python and Tcl exchange ``PyProcedureCall`` and ``TclProcedureResult`` messages
5. Python sends ``PyExit`` to terminate the Tcl tool or leave it open for interaction
6. Python waits for the subprocess to exit and cleans up temporary files

Communication protocol
----------------------

NoTcl uses three named pipes for communication:

- ``tcl2py``: Tcl to Python messages (command results, errors)
- ``py2tcl``: Python to Tcl messages (commands to execute)
- ``sentinel``: Child process liveness detection

**Pipe behavior:** The Tcl side opens and closes the data pipes (``tcl2py``/``py2tcl``) for every message. This design accommodates Tcl-based tools that interfere with open file descriptors (e.g., multi-threaded tools or those that fork subprocesses). The sentinel pipe remains open for the tool's entire lifetime.

**Why named pipes?** Unix domain sockets are not well-supported in Tcl. Named pipes (FIFOs) provide a portable, well-supported alternative.

Message format
--------------

Messages are lists of key-value pairs encoded as::

    key1
    base64(value1)
    key2
    base64(value2)
    ...

Keys and values are separated by newlines. Messages end with EOF (pipe close). Each message has a ``class`` key identifying the message type:

**Tcl to Python:**

- ``TclHello``: Initial handshake with Tcl version info
- ``TclProcedureResult``: Command result or error

**Python to Tcl:**

- ``PyProcedureCall``: Tcl command to execute
- ``PyExit``: Terminate or leave interactive

Child process monitoring
-------------------------

NoTcl detects unexpected child termination (crashes, explicit ``exit`` calls) using a sentinel named pipe. The Tcl side opens the write end at startup and keeps it open. The Python side monitors the read end with ``select()``. When the child dies, the OS closes the write end, making the read end readable (EOF), which Python detects immediately.

This approach has several advantages over signal-based detection:

- No process-global signal handlers (allows concurrent TclTool instances)
- No interference with user code that spawns subprocesses
- Thread-safe (works from any thread)
- Instant detection without polling

Return value preservation
-------------------------

All Tcl command return values are stored in a Tcl array (``$cmd_results``). When a :class:`~notcl.tclobj.TclRemoteObjRef` is passed back to Tcl, NoTcl uses the array reference (e.g., ``$cmd_results(42)``) rather than converting to a string. This preserves the internal representation and memory address of opaque handles, which some Tcl tools rely on for object identity.