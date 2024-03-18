# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import pytest
import subprocess
from .. import TclTool, TclError

class Tclsh(TclTool):
    def cmdline(self):
        return ["tclsh", self.script_name()]

def test_repr():
    with Tclsh(debug_py=True) as t:
        subprocess.check_call(["echo", "Test"])
        #print(out)
        ret = t.list("hello", "world")
        assert repr(ret) == "Tcl'hello world'"