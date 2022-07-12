from ..tclobj import encode

def test_obj1():
    o = encode(["hello", "world"])
    assert o == "{{hello} {world}}"

    o = encode("just a string")
    assert o  == "{just a string}"

    o = encode({"a": "b", "c":"d"})
    assert o == "{{a} {b} {c} {d}}"

    o = encode([1,2,3,"abc", "def"])
    assert o == "{{1} {2} {3} {abc} {def}}"