import io
import sys

import pytest

from acbox import utils


def test_load_mod(resolver):
    path = resolver.lookup("simple-script.py")

    mod = utils.loadmod(path, name="xyz.first")
    assert "xyz.first" in sys.modules
    assert "xyz.first" == mod.__name__
    assert str(path) == mod.__file__

    assert callable(mod.hello)


def test_load_mod_from_text():
    txt = """
def mult(value):
    return value * X
"""
    mod = utils.loadmod(io.StringIO(txt))
    pytest.raises(NameError, mod.mult, 12)

    mod = utils.loadmod(io.StringIO(txt), {"X": 2}, name="xyz.second")
    assert "xyz.second" in sys.modules
    assert "xyz.second" == mod.__name__
    assert "<string>" == mod.__file__

    assert callable(mod.mult)
    assert 24 == mod.mult(12)


def test_load_remote():
    mod = utils.loadmod("https://raw.githubusercontent.com/cav71/acbox/refs/heads/main/tests/test_utils.py")

    assert hasattr(mod, "test_load_remote")
    assert "<string https://raw.githubusercontent.com/cav71/acbox/refs/heads/main/tests/test_utils.py>" == mod.__file__


def test_diffdict():
    left = {
        "a": 1,
        "b": 2,
    }
    right = {
        "b": 2,
        "c": 3,
    }
    assert utils.diffdict(left, right, na=utils.NA) == {"a": (1, utils.NA), "c": (utils.NA, 3)}
    assert utils.diffdict(left, right, na="N/A") == {"a": (1, "N/A"), "c": ("N/A", 3)}
    assert utils.diffdict(left, right, {"a"}, na="N/A") == {"c": ("N/A", 3)}
