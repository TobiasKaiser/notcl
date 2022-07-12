Motivation
==========

What advantages does Python & NoTcl have over normal Tcl scripting?

- Opinion: Python is better suited for developing complex software. With its better encapsulation and abstraction mechanisms, Python scripts can be shorter, easier to understand and easier to maintain.
- A single Python interpreter version can be used to script Tcl tools with different Tcl versions and feature sets. This eliminates compatibility issues with Tcl code that is shared between tools with different Tcl versions.
- Different tools can be invoked (sequentially) by the same Python interpreter. This makes it easier to share data between tool invocations.

Related software
----------------

There are other software packages that have a similar aim as NoTcl, see the article `Accessing Tcl and Python from one another`_ in the Tcl wiki.

- tohil_ provides a bidirectional interface between Tcl and Python. It also requires to compile and integrate a C extension library, and might thus not be suitable for all Tcl-based tools. Its codebase is structured in an unusual way.
- libtclpy_ provides access in the reverse direction, controlling a Python interpreter from Tcl. It is a C extension library for Tcl, and might thus be difficult to integrate with some Tcl-based tools.
- tclpython_ is similar to libtclpy, providing access to a Python interpreter from Tcl. With tclpython, the Tcl interpreter and Python interpreter seem to share a single process.

Key features of NoTcl
---------------------

The following features differentiate NoTcl from the other Python-Tcl interfaces discussed above:

- Minimally invasive to Tcl tool: The Tcl-based tool executes only a small Tcl script that is responsible for communication with the controlling Python process. No C extension needs to be compiled and loaded in Tcl.
- References to all return values of Tcl commands are kept in a Tcl array. This makes it possible to maintain `opaque handles`_, pointers to internal data structures of the Tcl-tool, in Python and seamlessly pass them back to Tcl. This works even when conversion between strings and handles is poorly handled by the Tcl-based tool, because the handles' internal representations are preserved.

.. _Accessing Tcl and Python from one another: https://wiki.tcl-lang.org/page/Accessing+Tcl+and+Python+from+one+another
.. _libtclpy: https://github.com/aidanhs/libtclpy
.. _tohil: https://github.com/flightaware/tohil
.. _tclpython: https://github.com/amykyta3/tclpython/
.. _opaque handles: https://wiki.tcl-lang.org/page/Tcl+Handles