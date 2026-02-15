# SPDX-FileCopyrightText: 2026 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import subprocess
from .. import TclTool, TclError

class Tclsh(TclTool):
    def cmdline(self):
        return ["tclsh", self.script_name()]

def test_subprocess_inside_context():
    """subprocess.check_output must work inside a TclTool context without
    interfering with the Tcl child process."""
    with Tclsh() as t:
        output = subprocess.check_output(["echo", "Test"])
        assert output.strip() == b"Test"
        ret = t.list("hello", "world")
        assert repr(ret) == "Tcl'hello world'"

def test_nested_contexts():
    """Two TclTool contexts can be nested without interfering."""
    with Tclsh() as outer:
        outer.set("x", 1)
        with Tclsh() as inner:
            inner.set("x", 2)
            assert int(inner.set("x")) == 2
        assert int(outer.set("x")) == 1

def test_parallel_contexts():
    """Two TclTool contexts can be used side by side."""
    with Tclsh() as a, Tclsh() as b:
        a.set("x", "from_a")
        b.set("x", "from_b")
        assert str(a.set("x")) == "from_a"
        assert str(b.set("x")) == "from_b"
