Tests
=====

NoTcl comes with some tests. They can be run with :code:`pytest .`.

To run all tests, you need to compile the custom Tcl shell that is found in the folder *utils/test-notcl-tclsh/*. Tcl development headers are required for this (package *tcl-dev* in Debian / Ubuntu). Compile by running :code:`make`, then add the folder in which the executable *test-notcl-tclsh* resides to PATH when running Pytest. When *test-notcl-tclsh* is not found, the corresponding tests are skipped.