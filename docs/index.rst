NoTcl: Replace Tcl scripting with Python
========================================

Many software tools, especially in VLSI / digital circuit design, expose their functionality through a custom Tcl interpreter. In order to automate those programs, users are expected to write Tcl scripts. With growing complexity, such Tcl scripts often become difficult to maintain and do not integrate well into the context in which the tools are used.

With the NoTcl library, Tcl-based tools can be automated using Python. This makes it possible to use Tcl-based tools without Tcl-based scripting. See :doc:`motivation` for why this might be a good idea.

This software was developed during my doctoral studies at the Mixed Signal Circuit Design group, TU Berlin.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   apps_examples
   motivation
   api_reference
   under_the_hood
   tests
   known_issues

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
