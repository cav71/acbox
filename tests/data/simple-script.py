import sys

VALUE = 123


def hello(msg):
    print(f"Hi {msg}")


def hello_stderr(msg):
    print(f"Hi stderr {msg}", file=sys.stderr)


if __name__ == "__main__":
    hello("Antonio")
    hello_stderr("Antonio")
