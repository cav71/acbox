import pytest


@pytest.fixture(scope="function")
def loader(resolver):
    from acbox.loader import LoaderBase

    yield LoaderBase([resolver.root.parent])


def test_base(resolver, loader):
    target = resolver.lookup("simple-script.py")
    found = loader.lookup("data/simple-script.py")
    assert target == found


def test_load_data(loader):
    assert {"A": 1, "B": {"C": 2, "D": 3}} == loader.load("data/sample.json")
    assert {"A": 1, "B": {"C": 2, "D": 3}} == loader.load("data/sample.yml")
