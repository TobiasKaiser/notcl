from .. import TclTool

class Yosys(TclTool):
    def cmdline(self):
        return ["yosys", "-c", self.script_name()]