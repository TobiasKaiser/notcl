Usage
=====

Quick Start with Predefined Tools
----------------------------------

NoTcl provides ready-to-use interfaces for common EDA tools in the ``notcl.apps`` module::

    from notcl.apps import Yosys

    with Yosys() as y:
        y('yosys -import')  # Makes yosys commands accessible without prefix
        y.read_verilog('design.v')
        y.synth()
        y.write_json('output.json')

See :doc:`apps_examples` for more examples with Vivado, Yosys, and other tools.

Declaring a Custom TclTool
---------------------------

To use a Tcl-based tool not already provided in ``notcl.apps``, create a subclass of :class:`~notcl.TclTool` and define its ``cmdline`` method::

    from notcl import TclTool

    class Tclsh(TclTool):
        def cmdline(self):
            return ["tclsh", self.script_name()]

The ``cmdline`` method returns a list containing the executable name and its command line arguments. In this example, our Tcl-based tool is just the plain Tcl shell ``tclsh``. Other tools will require a different executable name and different arguments. The invoked tool needs to execute a particular Tcl script at startup. The filename of this script is returned by :meth:`~notcl.TclTool.script_name`.

Running a TclTool
-----------------

The Tcl-based tool is accessed by instantiating it and entering a *with* block::

    with Tclsh() as t:
        v = t("expr 3 * 5")
        print(v)

The result should be 15.

``t`` is a :class:`~notcl.tcltool.TclToolInterface` object. To evaluate Tcl code within the tool, call this object with a Tcl code string as argument.

When the ``with`` block is entered, a separate subprocess is spawned running the Tcl tool. The communication between Tcl and Python processes is explained in :doc:`under_the_hood`. Leaving the ``with`` block waits for the Tcl tool to terminate. The Tcl tool is terminated automatically, unless the ``interact`` flag is set to True.

:class:`~notcl.TclTool` accepts several constructor parameters for controlling logging, working directory, and interactive mode. See the :doc:`api_reference` for details.

Calling Tcl Commands
--------------------

:class:`~notcl.tcltool.TclToolInterface` allows Tcl commands to be called as Python methods. The following two lines are equivalent::

    v = t("expr 3 * 5")
    v = t.expr(3, "*", 5)

The second line calls ``t.expr`` as a method. The method name is prepended to its arguments and sent to Tcl as a string. Methods of :class:`~notcl.tcltool.TclToolInterface` are not explicitly specified anywhere — any method name becomes a Tcl command invocation.

**Automatic type conversion:** Python lists and dictionaries are automatically converted to Tcl-friendly strings when passed as arguments. The following three lines are equivalent::

    v = t("lreverse {1 2 3}")
    v = t.lreverse("1 2 3")
    v = t.lreverse([1, 2, 3])

**Keyword arguments:** Keyword arguments are converted to the flag-based syntax commonly used in Tcl::

    t.myfunc("arg1", param1="value1", param2="value2")
    # Resulting Tcl call: 'myfunc arg1 -param1 value1 -param2 value2'

Setting a keyword parameter to True generates a flag without a value::

    t.myfunc("arg1", myflag=True)
    # Resulting Tcl call: 'myfunc -myflag'

**Note:** Setting a parameter to False omits it entirely from the Tcl command. If you need explicit ``-flag false`` syntax, pass the string ``"false"`` instead of the Python boolean.

Working with Return Values
--------------------------

Return values from Tcl are wrapped in :class:`~notcl.tclobj.TclRemoteObjRef` objects. A Tcl return value is fundamentally a string, and without additional type information, NoTcl cannot automatically convert it to Python data structures.

**Converting to Python types:** :class:`~notcl.tclobj.TclRemoteObjRef` objects can be converted to Python types::

    v = t.expr(3, "*", 5)
    print(str(v))    # "15"
    print(int(v))    # 15
    print(float(v))  # 15.0

**Passing return values back to Tcl:** When a :class:`~notcl.tclobj.TclRemoteObjRef` is passed back to Tcl via method calls, NoTcl uses a reference to the original Tcl object rather than creating a new string. This preserves the internal representation and object address of opaque handles, which some Tcl-based tools rely on::

    handle = t.create_some_object()
    t.modify_object(handle)  # Uses $cmd_results(N) reference in Tcl
    t.delete_object(handle)

For explicit control, use :meth:`~notcl.tclobj.TclRemoteObjRef.ref_str` to get the Tcl reference string::

    handle = t.create_some_object()
    t(f"puts {handle.ref_str()}")  # Explicitly uses $cmd_results(N)

Error Handling
--------------

When a Tcl command fails, a :class:`~notcl.TclError` exception is raised in Python. The Tcl tool remains usable after catching the error::

    from notcl import TclError

    with Tclsh() as t:
        try:
            t.expr("invalid")
        except TclError as e:
            print(f"Tcl error: {e}")

        # Tool is still usable
        result = t.expr(1, "+", 1)

If the Tcl subprocess terminates unexpectedly (e.g., crashes or calls ``exit``), a :class:`~notcl.ChildProcessEarlyExit` exception is raised::

    from notcl import ChildProcessEarlyExit

    try:
        with Tclsh() as t:
            t.exit(0)  # Tcl process terminates
            t.expr(1, "+", 1)  # This line is never reached
    except ChildProcessEarlyExit:
        print("Tcl process exited early")