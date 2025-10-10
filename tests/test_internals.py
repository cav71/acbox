def test_script_lookup(resolver):
    path = resolver.lookup("simple-script.py")
    assert path
    assert path.exists()


def test_script_load(resolver):
    data = resolver.load("simple-script.py", "text")
    assert (
        data[:525]
        == """
# call this:
#   simple-script.py - writes simple messages to stdout/stderr
#   VALUE=123 simple-script.py - same as above, but writes VALUE message too
#   WAIT=2 VALUE=123 simple-script.py - same as above, but wait 2s before printing last message
#   ABORT=12 simple-script.py - same as above, but abort the script with error code 12
import os
import sys
import time
from typing import TextIO


def hello(index: int, msg: str, file: TextIO = sys.stdout) -> None:
    print(f"{index}, got '{msg}' ({file.name})", file=file)
""".lstrip()
    )

    mod = resolver.load("simple-script.py", "mod")
    assert callable(mod.hello)
