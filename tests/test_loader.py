import inspect
from types import ModuleType

import pytest

import acbox.loader

yaml: ModuleType | None = None
try:
    import yaml
except ImportError:
    pass


@pytest.fixture(scope="function")
def loader(resolver):

    yield acbox.loader.LoaderBase([resolver.root.parent])


def test_loader_vs_resolver_lookup(resolver, loader):
    expected = resolver.lookup("loader/sample.py")
    assert expected == resolver.lookup("sample.py")
    assert expected.exists()

    assert expected == loader.lookup("data/loader/sample.py")

    pytest.raises(FileNotFoundError, resolver.lookup, "xwew")
    pytest.raises(FileNotFoundError, loader.lookup, "xwew", abort=True)
    assert loader.lookup("xwew") is None


def test_loader_vs_resolver_load(resolver, loader):
    assert {"A": 1, "B": {"C": 2, "D": 3}} == resolver.load("loader/sample.json")
    assert {"A": 1, "B": {"C": 2, "D": 3}} == loader.load("data/loader/sample.json")


@pytest.mark.skipif(not yaml, reason="need to install pyyaml")
def test_loader_vs_resolver_load_yaml(resolver, loader):
    assert {"A": 1, "B": {"C": 2, "D": 3}} == resolver.load("loader/sample.yml")
    assert {"A": 1, "B": {"C": 2, "D": 3}} == loader.load("data/loader/sample.yml")


def test_loader_vs_resolver_load_mod(loader):
    pytest.raises(TypeError, loader.load, "data/loader/sample.py")

    mod = loader.load("data/loader/sample.py", mode="mod")
    assert """\
def hello(name: str) -> None:
    print(f"Hi {name}")
""" == inspect.getsource(mod)

    assert """\
def hello(name: str) -> None:
    print(f"Hi {name}")
""" == loader.load("data/loader/sample.py", mode="text")
