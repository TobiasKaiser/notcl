import pytest
import subprocess
from .. import TclTool, TclError

class Tclsh(TclTool):
    def cmdline(self):
        return ["tclsh", self.script_name()]

def test_set_string():
    with Tclsh() as t:
        t.set("myvar", "ThisIsATest")
        v=t.set("myvar")
        assert str(v) == "ThisIsATest"

def test_set_int():
    with Tclsh() as t:
        t.set("myvar", 123459)
        v=t.set("myvar")
        assert int(v) == 123459

def test_set_float():
    with Tclsh() as t:
        t.set("myvar", 3.14)
        v=t.set("myvar")
        assert abs(float(v) - 3.14) < 0.01 


def test_expr():
    with Tclsh() as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11

def test_list_of_strings():
    with Tclsh() as t:
        v=t.lreverse(["one", "two", "three"])
        assert str(v).split(" ") == ["three", "two", "one"]

def test_list_of_ints():
    with Tclsh() as t:
        v=t.lreverse([5,6,7])
        assert list(map(int, str(v).split(" "))) == [7,6,5]


def test_dict():
    with Tclsh() as t:
        v=t.dict("merge", {"key1":"value1"}, {"key2":"value2", "key3":"value3"})
        assert str(v).split(" ") == ["key1", "value1", "key2", "value2", "key3", "value3"]

def test_expr_log_commands_fancy(capsys):
    with Tclsh(log_commands=True, log_fancy=True) as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11
    cap = capsys.readouterr()
    assert cap.out == "\x1b[93m[notcl]\x1b[0m Cmd:\x1b[0m expr {9} {+} {3} {*} {11}\n"
    assert cap.err == ""

def test_expr_log_commands_plain(capsys):
    with Tclsh(log_commands=True, log_fancy=False) as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11
    cap = capsys.readouterr()
    assert cap.out == "[notcl] Cmd: expr {9} {+} {3} {*} {11}\n"
    assert cap.err == ""

def test_expr_log_commands_disabled(capsys):
    with Tclsh(log_commands=False) as t:
        v=t.expr(9, '+', 3, '*', 11)
        assert int(v) == 9+3*11
    cap = capsys.readouterr()
    assert cap.out == ""
    assert cap.err == ""

def test_explicit_ref():
    with Tclsh() as t:
        v1=t("expr 44 - 2")
        v2=t(f"expr {v1.ref_str()} / 2")
        assert int(v2) == 21
        v3=t(f"format Hello%i {v2.ref_str()}")
        assert str(v3) == "Hello21"

def test_implicit_ref():
    with Tclsh() as t:
        v1=t.expr(44, '-', 2)
        v2=t.expr(v1, '/', 2) 
        assert int(v2) == 21
        v3=t.format("Hello%i", v2)
        assert str(v3) == "Hello21"

def test_tclerror():
    with Tclsh() as t:
        with pytest.raises(TclError):
            t.expr("*", "+")

        with pytest.raises(TclError):
            t("does_not_exist")

        v=t.expr(1, '+', 1)
        assert int(v)==2

def test_lists():
    with Tclsh() as t:
        ret = t.list(1,2,3)
        assert str(ret) == '1 2 3'

def test_boolargs():
    with Tclsh() as t:
        ret = t.list(myarg=True)
        assert str(ret) == '-myarg'

        ret = t.list(myarg=False)
        assert str(ret) == ''

def test_repr():
    with Tclsh() as t:
        ret = t.list("hello", "world")
        assert repr(ret) == "Tcl'hello world'"

def test_child_terminates_nonzero():
    reaches1 = False
    reaches2 = False
    with pytest.raises(subprocess.CalledProcessError):
        with Tclsh() as t:
            reaches1 = True
            v=t.exit(1)
            reaches2 = True

    assert reaches1
    assert not reaches2

def test_child_terminates_zero():
    reaches1 = False
    reaches2 = False
    with pytest.raises(subprocess.CalledProcessError):
        with Tclsh() as t:
            reaches1 = True
            v=t.exit(0)
            reaches2 = True

    assert reaches1
    assert not reaches2

def test_context_forwards_excepts():
    with pytest.raises(ValueError):
        with Tclsh() as t:
            raise ValueError("test")  