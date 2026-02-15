# NoTcl: Replace Tcl scripting with Python

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![NoTcl on PyPI](https://img.shields.io/pypi/v/notcl.svg)](https://pypi.python.org/pypi/notcl)
[![Documentation Status](https://readthedocs.org/projects/notcl/badge/?version=latest)](https://notcl.readthedocs.io/en/latest/?badge=latest)

Many tools, especially in VLSI and digital circuit design, expose their functionality through a custom Tcl interpreter. In order to automate those programs, users are expected to write Tcl scripts. With growing complexity, such Tcl scripts become difficult to maintain and often do not integrate seamlessly into larger software systems.

NoTcl allows Tcl-based tools to be automated using Python instead of Tcl. It wraps each tool in a Python interface, turning it into a library that can be imported, tested, and integrated like any other Python package. Python's module system, testing frameworks, and rich ecosystem make it better suited for complex automation than Tcl scripts. NoTcl handles subprocess management and communication via named pipes, exposing a Python API for calling Tcl commands.

## Installation

```bash
pip3 install notcl
```

## Quick Start

Define a custom tool by subclassing `TclTool`:

```python
from notcl import TclTool

class Tclsh(TclTool):
    def cmdline(self):
        return ["tclsh", self.script_name()]

with Tclsh() as t:
    result = t.expr(3, "*", 5)  # Call Tcl commands as Python methods
    print(result)  # 15

    items = t.lreverse([1, 2, 3])  # Automatic type conversion
```

To dive in deeper, please have a look at the **[documentation](https://notcl.readthedocs.io)**.

## Related Tools

- **[pydesignflow](https://github.com/TobiasKaiser/pydesignflow)** — A technology- and tool-agnostic micro-framework for constructing FPGA and VLSI design flows in Python. Uses NoTcl to automate Tcl-based EDA tools like Yosys and OpenROAD.

## Example Projects

- **[RISC-V Lab](https://github.com/tub-msc/rvlab)**: An FPGA-based RISC-V design platform and flow for teaching SoC development, using PyDesignFlow to manage hardware synthesis, simulation, and software builds..

## License

Copyright 2022 - 2026 Tobias Kaiser

SPDX-License-Identifier: Apache-2.0
