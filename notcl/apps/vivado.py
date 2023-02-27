from .. import TclTool
from pathlib import Path
import os

class Vivado(TclTool):
    def cmdline(self):
        return ["vivado",
            "-mode", "tcl",
            "-nojournal",
            "-source", self.script_name()
        ]

    @staticmethod    
    def vivado_dir() -> Path:
        """
        Returns the XILINX_VIVADO Path, e.g. for locating Verilog files of
        the Xilinx cell libraries.
        """
        return Path(os.environ["XILINX_VIVADO"])