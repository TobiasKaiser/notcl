import pytest
import shutil
from .. import TclTool, TclError

class CustomTclsh(TclTool):
    tclsh_name = "test-notcl-tclsh"

    def cmdline(self):
        return [self.tclsh_name, self.script_name()]

    @classmethod
    def exists(cls):
        return shutil.which(cls.tclsh_name) != None

    @classmethod
    def require(cls):
        if not cls.exists():
            pytest.skip("test-notcl-tclsh, which is required for test, was not found in PATH.")


def test_expr():
    CustomTclsh.require()

    with CustomTclsh() as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11

def test_box_ref():
    CustomTclsh.require()
    
    with CustomTclsh() as t:
        mybox = t.create_box(999)
        v = t.unwrap_box(mybox)
        assert int(v) == 999

def test_box_ref_by_string():
    CustomTclsh.require()
    
    with CustomTclsh() as t:
        mybox = t.create_box(5432)
        mybox_str = str(mybox)
        with pytest.raises(TclError):
            t.unwrap_box(mybox_str)

        v = t.unwrap_box(mybox)
        assert int(v)==5432


def test_box_ref_multiple():
    CustomTclsh.require()
    
    with CustomTclsh() as t:
        box1 = t.create_box(1234)
        box2 = t.create_box(5678)
        box3 = t.create_box(9012)
        v = t.unwrap_box(box1)
        assert int(v) == 1234
        v = t.unwrap_box(box3)
        assert int(v) == 9012
        v = t.unwrap_box(box2)
        assert int(v) == 5678

if __name__=="__main__":
    test_tclsh()