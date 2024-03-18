from .. import TclTool

class Tclsh(TclTool):
    def cmdline(self):
        return ["tclsh", self.script_name()]

#def test_abort_on_error():
with Tclsh(abort_on_error=False, interact=True, debug_py=True, debug_tcl=True) as t:
    t.does_not_exist("bla")
    