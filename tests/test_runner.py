from __future__ import annotations

import sys

from acbox import runner


def test_stderr_stdout(resolver):
    exe = resolver.lookup("test-script.py")

    runc = runner.Runner(verbose=False)
    out = runc([sys.executable, exe], capture=True)

    assert (
        out.strip().replace("\r", "")
        == """
HELLO=N/A
line (out) 1
line (out) 2
line (out) 4
line (out) 5
line (out) 7
line (out) 8
""".strip().replace("\r", "")
    )

    out = runc([sys.executable, exe], overrides={"HELLO": "123"}, capture=True)
    assert (
        out.strip().replace("\r", "")
        == """
HELLO=123
line (out) 1
line (out) 2
line (out) 4
line (out) 5
line (out) 7
line (out) 8
""".strip().replace("\r", "")
    )
