Known Issues
============

Limitations and quirks:

1. References to all return values of Tcl commands are maintained in Tcl, purposefully preventing garbage collection in Tcl. This is not a big concern for Tcl tools that perform a limited sequence of tasks and then terminate, but can be seen as a problematic memory leak in other cases.
2. Be careful when passing bools to Tcl commands using the Python-style interface: :code:`t.myfunc(myflag=True)` leads to the Tcl command :code:`myfunc -myflag` and :code:`t.myfunc(myflag=False)` leads to the Tcl command :code:`myfunc`, omitting *myflag* entirely. If you need Tcl commands like :code:`myfunc -myflag true` and :code:`myfunc -myflag false`, pass *"true"* / *"false"* as strings.
