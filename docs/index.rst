NoTcl: Replace Tcl scripting with Python
========================================

Many software tools, especially in VLSI and digital circuit design, expose their functionality through a custom Tcl interpreter. In order to automate those programs, users are expected to write Tcl scripts. With growing complexity, such Tcl scripts often become difficult to maintain and do not integrate well into larger software systems. NoTcl allows Tcl-based tools to be automated using Python instead of Tcl. It wraps each tool in a Python interface, turning it into a library that can be imported, tested, and integrated like any other Python package.

To get started, see :doc:`usage` for installation and basic examples, or :doc:`apps_examples` for ready-to-use interfaces to common tools like Yosys and Vivado. The :doc:`background` section explains the advantages of Python-based automation and how NoTcl differs from other Tcl-Python bridges. The :doc:`api_reference` documents the complete API, while :doc:`under_the_hood` covers implementation details. Known limitations are listed in :doc:`known_issues`, and information about running tests is available in :doc:`tests`.

This software was developed during my doctoral studies at the Mixed Signal Circuit Design group, TU Berlin.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   apps_examples
   background
   api_reference
   under_the_hood
   tests
   known_issues

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
