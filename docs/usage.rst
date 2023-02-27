Usage
=====

Declaring a TclTool
-------------------

To use a specific Tcl-based tool with NoTcl, you must create a subclass of TclTool and define its *cmdline* method::
    
    from notcl import TclTool

    class Tclsh(TclTool):
        def cmdline(self):
            return ["tclsh", self.script_name()]

The *cmdline* method determines the name of the executable and its command line arguments. In this example, our Tcl-based tool is just the plain Tcl shell *tclsh*. Other tools will require a different executable name and different arguments. The invoked tool needs to execute a particular Tcl script at startup. The filename of this script is returned by *self.script_name()*.

Running the TclTool
-------------------

The Tcl-based tool can now be accessed by instantiating it and entering a  *with* block with the instance::
    
    with Tclsh() as t:
        v = t("expr 3 * 5")
        print(v)

The result should be 8.

*t* is a *TclToolInterface* object. To evaluate Tcl code within the tool, this object can be called with Tcl code as argument string.

When the *with* block is entered, the tool command is called, which means a separate process is spawned. The communication between Tcl and Python process is explained in :doc:`under_the_hood`. Leaving the *with* block wait for the Tcl tool to terminate. The Tcl tool is terminated automatically, unless TclTool's *interact* flag is set to True.

To better understand what is going on, pass :code:`log_commands='fancy'` at *Tclsh* instantiation. This causes all Tcl commands, their results and errors to be printed to stdout.

You can pass :code:`interact=True` to *Tclsh* to keep tclsh open at the end of the *with* block. In this case, the Python script waits for the user to terminate tclsh manually.

Syntactic sugar
---------------

*TclToolInterface* offers some syntactic sugar that allows reflecting Tcl commands semantically in Python.

Following two lines of code are equivalent::

    v = t("expr 3 * 5")
    v = t.expr(3, "*", 5)

The second line calls the *t.expr* method. The method name translates is prepended to its arguments and then sent to Tcl as a string. Methods of *TclToolInterface* are not explicitly specified anywhere. If a command or procedure of the given name does not exist in the Tcl context, an error is raised in Tcl and propagated to Python.

The following three lines of code are also equivalent, invoking Tcl's list reversal command *lreverse* in different ways from Python::

    v = t("lreverse {1 2 3}")
    v = t.lreverse("1 2 3")
    v = t.lreverse([1, 2, 3])

When passing values from Python to Tcl with a method call, *notcl.tclobj.encode* attempts to convert simple list structures that are passed as argument to Tcl-friendly strings. 

Keyword arguments are converted to a form commonly used in Tcl::

    t.myfunc("arg1", param1="value1", param2="value2")
    # resulting Tcl call: 'myfunc arg1 -param1 value1 -param2 value2'

Setting a keyword parameter to True omits its value in Tcl::
    
    t.myfunc("arg1", myflag=True)
    # resulting Tcl call: 'myfunc -myflag'

Tcl return values in Python
---------------------------

The Return value of a Tcl command or procedure is basically a string. Without knowledge about the structure or type of the return value, it is not possible to convert this string to a meaningful data structure such as a list or dict in Python.

Return values from Tcl are wrapped in *TclRemoteObjRef* objects. Passing a *TclRemoteObjRef* back to Tcl via *TclToolInterface* method calls causes the interpreter to use a reference that was maintained within the Tcl tool as argument, instead of passing a newly created string as argument. While this should not make a difference *in theory*, some Tcl-based tools rely on internal representations or object addresses of opaque handles to stay the same. A *TclRemoteObjRef* can be converted to a string via *str()*.