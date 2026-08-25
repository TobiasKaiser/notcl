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

The sentinel only works once the Tcl side has opened it. A tool that fails before it runs ``notcl.tcl`` at all (invalid command line arguments, missing license, ...) never does, and neither the sentinel nor the data pipes would ever become readable. To cover this case, Python additionally monitors the child process itself through a pidfd (``os.pidfd_open()``, Linux 5.3 and later), which becomes readable in the same ``select()`` calls when the process exits. This requires that the process spawned by ``cmdline()`` lives as long as the tool: a launcher script must ``exec`` the tool rather than fork it and exit. Without pidfd support, only the sentinel is monitored.

This approach has several advantages over signal-based detection:

- No SIGCHLD handler (allows concurrent TclTool instances)
- No interference with user code that spawns subprocesses
- Thread-safe (works from any thread)
- Instant detection without polling

Ctrl+C handling
---------------

A Ctrl+C in the terminal delivers SIGINT to the whole foreground process group, i.e. to Python and to all Tcl tools at the same time. Each Tcl tool handles the signal as it would interactively, typically by aborting its current command. Python must not react in the middle of a bridge transaction, as this would leave the Tcl tool without a communication partner, and it must not unwind a ``with`` block while another thread is still talking to that tool.

Python delivers signals to the main thread only, and ``KeyboardInterrupt`` can only be raised there. Therefore, while any :class:`~notcl.TclTool` context entered in the main thread is active (with ``handle_sigint=True``), NoTcl installs one process-wide SIGINT handler. Every bridge transaction - a command, the startup handshake, the shutdown of the tool - registers itself with this handler for its duration, from any thread. On SIGINT, the handler acts on the transactions in flight:

- If none is in flight, or the tools involved have exited already (there is no one to leave the signal to), ``KeyboardInterrupt`` is raised right away, like plain Python.
- Otherwise, the transactions in flight are marked as interrupted, and the signal is recorded as pending. A transaction in the main thread delivers it when it ends: ``TclError`` if the tool aborted the command, ``KeyboardInterrupt`` otherwise (see :doc:`usage`). If the last transaction in flight ends in another thread, that thread re-sends SIGINT to the main thread (``signal.pthread_kill``), so that the handler raises ``KeyboardInterrupt`` there, wherever the main thread is - including blocking calls such as ``Thread.join()``. A SIGINT received while waiting for an interactive tool to exit is discarded, as Ctrl+C at the tool's prompt is between the user and the tool.

The handler is removed again when the last main-thread context exits. Contexts entered in other threads cannot install a handler (Python permits this in the main thread only) and are covered as long as the handler is installed; without any main-thread context, Python's default handling applies, which does not touch a context owned by another thread. If an exception nevertheless escapes in the middle of a transaction (e.g. ``KeyboardInterrupt`` with ``handle_sigint=False``), the Tcl tool is terminated instead of being sent ``PyExit``.

Return value preservation
-------------------------

All Tcl command return values are stored in a Tcl array (``$cmd_results``). When a :class:`~notcl.tclobj.TclRemoteObjRef` is passed back to Tcl, NoTcl uses the array reference (e.g., ``$cmd_results(42)``) rather than converting to a string. This preserves the internal representation and memory address of opaque handles, which some Tcl tools rely on for object identity.