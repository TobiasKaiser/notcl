Applications & Examples
=======================

NoTcl's submodule *notcl.apps* provides predefined TclTool subclasses for some popular programs. If those predefined TclTool subclasses do not suffice, you can always define custom TclTool subclasses, as described in :doc:`usage`.
NoTcl comes with no warranties, so your mileage may vary.

In general, tools that embed the original Tcl interpreter version 8.5 or newer should work with NoTcl. For Tcl versions below 8.6, TclLib_'s base64_ module is required, but it is usually present and requires no separate installation.

.. _TclLib: https://wiki.tcl-lang.org/page/Tcllib
.. _base64: https://wiki.tcl-lang.org/page/base64

Yosys
-----

Tested with Yosys 0.23 (embeds Tcl 8.6). Example::

    from notcl.apps import Yosys

    with Yosys() as y:
        y('yosys -import') # Makes yosys commands accessible without prefix
        y.read_verilog('test.v')
        y.write_json('out.json')

Xilinx Vivado
-------------

Tested with Xilinx Vivado 2022.2 (embeds Tcl 8.5). Example::

    from notcl.apps import Vivado

    with Vivado() as t:
        t.read_verilog(["mydesign.v"])
        t.read_xdc("mydesign.xdc")
        t.synth_design(top="mydesign", part="xc7a200tsbg484-1")
        t.write_checkpoint("out.dcp")

TODO: Support for Vivado's Logic Simulator XSIM.

Questa logic simulator
----------------------

TODO

Synopsys Design Tools
---------------------

TODO: IC Compiler 2 (icc2_shell), Design Compiler (dc_shell).

Not Supported
-------------

The following tools seem not to work with NoTcl:

- OpenOCD, which uses Jim Tcl instead of the original Tcl interpreter