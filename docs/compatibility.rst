Compatibility
=============

This page shows the tools with which NoTcl was found working. NoTcl and this list comes with no warranties, so your mileage may vary.

In general, tools that embed the Tcl interpreter versin 8.5 or newer should work. For Tcl versions below 8.6, TclLib_'s base64_ module is required, but it is usually present and requires no separate installation.

+-----------------------------------------+--------------+--------------+-------------------+
| Software                                | Commands     | Embedded Tcl | Works with NoTcl? |
+=========================================+==============+==============+===================+
| Yosys 0.23                              | yosys        | Tcl 8.6      | yes               |
+-----------------------------------------+--------------+--------------+-------------------+
| Xilinx Vivado 2022.2                    | vivado, xsim | Tcl 8.5      | yes               |
+-----------------------------------------+--------------+--------------+-------------------+
| Siemens / Mentor Graphics Questa 2022.1 | vsim         | Tcl 8.6      | yes               |
+-----------------------------------------+--------------+--------------+-------------------+
| OpenOCD                                 | openocd      | Jim Tcl      | no                |
+-----------------------------------------+--------------+--------------+-------------------+

.. _TclLib: https://wiki.tcl-lang.org/page/Tcllib
.. _base64: https://wiki.tcl-lang.org/page/base64