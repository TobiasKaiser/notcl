NoTcl: Replace Tcl scripting with Python
========================================

.. image:: https://readthedocs.org/projects/notcl/badge/?version=latest
    :target: https://notcl.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

Many tools, especially in VLSI / digital circuit design, expose their functionality through a custom Tcl interpreter. In order to automate those programs, users are expected to write Tcl scripts. With growing complexity, such Tcl scripts become difficult to maintain and often do not integrate seamlessly into the context, in which the tools are used.

With the NoTcl library, Tcl-based tools can be automated using Python. This makes it possible to use Tcl-based tools without Tcl-based scripting.

You can install NoTcl using pip: :code:`pip3 install notcl`

Minimal example::
    
    from notcl import TclTool

    class Tclsh(TclTool):
        def cmdline(self):
            return ["tclsh", self.script_name()]

    with Tclsh() as t:
        v = t("expr 3 * 5")
        print(v)

Full documentation is found at https://notcl.readthedocs.io or in the *docs/* folder.


License
-------

Copyright 2022 Tobias Kaiser

SPDX-License-Identifier: Apache-2.0