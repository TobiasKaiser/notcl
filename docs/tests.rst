Tests
=====

NoTcl includes a comprehensive test suite covering core functionality, concurrency, and integration with Tcl tools.

Running the tests
-----------------

To run all tests from the project root::

    pytest notcl/tests/

Or with verbose output::

    pytest notcl/tests/ -v

Test requirements
-----------------

Most tests require a Tcl shell to be available. NoTcl includes a custom test shell in ``utils/test-notcl-tclsh/`` that provides additional test commands.

To compile the test shell:

1. Install Tcl development headers (package ``tcl-dev`` on Debian/Ubuntu)
2. Navigate to ``utils/test-notcl-tclsh/``
3. Run ``make``
4. Add the directory to PATH when running pytest:

   .. code-block:: bash

       PATH=$PATH:/path/to/notcl/utils/test-notcl-tclsh pytest notcl/tests/

When the test shell is not found, tests requiring it are automatically skipped.

Test coverage
-------------

The test suite includes:

- **Basic functionality** (``test_tclsh.py``): Command evaluation, type conversion, error handling, return value references
- **Concurrency** (``test_concurrency.py``): Nested contexts, parallel tool instances, subprocess compatibility
- **Bridge communication** (``test_bridge.py``): Low-level message passing between Python and Tcl
- **Custom tools** (``test_custom_tclsh.py``): TclRemoteObjRef features, object-oriented API usage
- **Type encoding** (``test_tclobj.py``): Python to Tcl data structure conversion

All tests use the standard Tcl shell (``tclsh``) as the simplest possible Tcl-based tool, ensuring the library works correctly with minimal dependencies.