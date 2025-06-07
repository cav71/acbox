def test_script_lookup(resolver):
    path = resolver.lookup("simple-script.py")
    assert path
    assert path.exists()


def test_script_load(resolver):
    data = resolver.load("simple-script.py", "text")
    assert (
        data
        == """
VALUE = 123


def hello(msg):
    print(f"Hi {msg}")
""".lstrip()
    )

    mod = resolver.load("simple-script.py", "mod")
    assert mod.VALUE, 123
