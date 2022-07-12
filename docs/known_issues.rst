Known Issues
============

Limitations and quirks:

1. Running more than one TclTool at a time will lead to problems due to the way in which signal handling is currently done.
2. While a TclTool is running, the Python process will ignore Ctrl+C / SIGINT events. An unresponsive TclTool will cause the controlling Python script to block until the TclTool terminates. If the TclTool does not respond to Ctrl+C / Ctrl+D, it needs to be killed manually. After TclTool termination, the Python process is configured to respond to Ctrl+C / SIGINT again.  
3. References to all return values of Tcl commands are maintained in Tcl. This purposefully prevents garbage collection in Tcl, but leads to possibly avoidable use of memory in Tcl. This is not a big concern for Tcl tools that perform one-shot tasks and then terminate, but can be problematic in other cases.