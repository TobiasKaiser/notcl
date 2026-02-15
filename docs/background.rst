Background
==========

Why replace Tcl with Python?
----------------------------

Many VLSI and EDA tools expose their functionality through a custom Tcl
interpreter. As automation scripts for these tools grow in complexity, Tcl's
limited abstraction and encapsulation mechanisms make them increasingly
difficult to maintain.

NoTcl allows these tools to be scripted in Python instead, which offers several
practical advantages:

- **Better language support for complex automation.** Python's module system,
  exception handling, and standard library make it easier to write, test, and
  maintain large automation scripts.
- **Tcl-based tools become Python libraries.** NoTcl wraps each tool in a
  Python interface, allowing tool functionality to be imported and used like
  any other Python library, integrated into larger Python applications.
- **Tool-independent Python interpreter across tools.** Different EDA tools
  embed different Tcl versions with varying feature sets. Shared Tcl code
  between tools often requires version-specific workarounds. With NoTcl, all
  tool-specific logic is expressed in Python, eliminating Tcl version
  compatibility issues.
- **Straightforward data sharing between tools.** When multiple tools are
  invoked sequentially from the same Python process, intermediate results can
  be passed between them using ordinary Python data structures.

How NoTcl differs from other approaches
----------------------------------------

Several other projects bridge Tcl and Python (see `Accessing Tcl and Python
from one another`_ in the Tcl wiki). NoTcl differs from these in two key ways:

1. **No C extensions required.** The Tcl tool executes only a small, pure-Tcl
   communication script. There is no need to compile or load a shared library
   into the tool's Tcl interpreter, which makes NoTcl compatible with
   tools that do not support loading custom C extensions.

2. **Opaque handle preservation.** References to all Tcl command return values
   are kept in a Tcl array, allowing `opaque handles`_ (pointers to internal
   data structures) to be held in Python and passed back to Tcl without
   losing their internal representation. This matters for tools that
   distinguish handles from their string representations.

Related projects:

- tohil_ provides a bidirectional Tcl-Python interface via a C extension.
- libtclpy_ embeds Python inside Tcl via a C extension.
- tclpython_ also embeds Python inside Tcl, sharing a single process.

.. _Accessing Tcl and Python from one another: https://wiki.tcl-lang.org/page/Accessing+Tcl+and+Python+from+one+another
.. _libtclpy: https://github.com/aidanhs/libtclpy
.. _tohil: https://github.com/flightaware/tohil
.. _tclpython: https://github.com/amykyta3/tclpython/
.. _opaque handles: https://wiki.tcl-lang.org/page/Tcl+Handles
