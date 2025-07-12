import copy

from acbox import dictionaries


def roundtrip(data, updates):
    original = copy.deepcopy(data)
    undo = dictionaries.dictupdate(data, updates)
    dictionaries.dictrollback(data, undo)
    assert data == original


def test_first():
    original = {}
    updates = [
        ("a.b.c.d.e", 1),
    ]

    data = copy.deepcopy(original)
    undo = dictionaries.dictupdate(data, updates)
    assert undo == [
        ("a", dictionaries.DELETE),
        ("a.b", dictionaries.DELETE),
        ("a.b.c", dictionaries.DELETE),
        ("a.b.c.d", dictionaries.DELETE),
        ("a.b.c.d.e", dictionaries.DELETE),
    ]
    assert data == {
        "a": {
            "b": {
                "c": {
                    "d": {
                        "e": 1,
                    }
                }
            }
        }
    }
    dictionaries.dictrollback(data, undo)
    assert data == original


def test_second():
    data = {
        "a": 12,
        "c": {
            "x": 99,
        },
    }

    updates = [
        ("a", 22),
        ("d.e", 33),
        ("c.y.z", 44),
        ("c.x", 55),
    ]

    original = copy.deepcopy(data)
    undo = dictionaries.dictupdate(data, updates)
    assert undo == [
        ("a", 12),
        ("d", dictionaries.DELETE),
        ("d.e", dictionaries.DELETE),
        ("c.y", dictionaries.DELETE),
        ("c.y.z", dictionaries.DELETE),
        ("c.x", 99),
    ]
    assert data == {
        "a": 22,
        "c": {
            "y": {
                "z": 44,
            },
            "x": 55,
        },
        "d": {
            "e": 33,
        },
    }

    dictionaries.dictrollback(data, undo)
    assert data == original


def test_third():
    data = {
        "a": 12,
        "c": {
            "x": 99,
        },
    }

    updates = [
        ("c.y.z", 44),
        ("c.x", dictionaries.DELETE),
    ]

    original = copy.deepcopy(data)
    undo = dictionaries.dictupdate(data, updates)
    assert data == {
        "a": 12,
        "c": {
            "y": {
                "z": 44,
            },
        },
    }
    dictionaries.dictrollback(data, undo)
    assert data == original
