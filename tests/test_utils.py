from acbox import utils


def test_load_mod(resolver):
    path = resolver.lookup("simple-script.py")

    mod = utils.loadmod(path)
    assert mod.VALUE, 123


def test_load_remote():
    mod = utils.loadmod("https://raw.githubusercontent.com/cav71/acbox/refs/heads/main/tests/test_utils.py")
    assert hasattr(mod, "test_load_remote")


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
