from acbox import utils


def test_load_mod(resolver):
    path = resolver.lookup("simple-script.py")

    mod = utils.loadmod(path)
    assert mod.VALUE, 123


def test_load_remote():
    mod = utils.loadmod("https://raw.githubusercontent.com/cav71/acbox/refs/heads/main/tests/test_utils.py")
    assert hasattr(mod, "test_load_remote")
