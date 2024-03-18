# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from .. import TclTool

class Yosys(TclTool):
    def cmdline(self):
        return ["yosys", "-c", self.script_name()]