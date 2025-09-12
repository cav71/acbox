def test_script_lookup(resolver):
    path = resolver.lookup("simple-script.py")
    assert path
    assert path.exists()


def test_script_load(resolver):
    data = resolver.load("simple-script.py", "text")
    assert (
        data
        == """
import sys

VALUE = 123


def hello(msg):
    print(f"Hi {msg}")


def hello_stderr(msg):
    print(f"Hi stderr {msg}", file=sys.stderr)


if __name__ == "__main__":
    hello("Antonio")
    hello_stderr("Antonio")
""".lstrip()
    )

    mod = resolver.load("simple-script.py", "mod")
    assert mod.VALUE, 123
