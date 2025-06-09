from __future__ import annotations

import sys

from acbox import runner


def test_stderr_stdout(resolver):
    exe = resolver.lookup("test-script.py")
    out, err = runner.runc([sys.executable, exe])
    assert (
        out
        == """
HELLO=N/A
line (out) 1
line (out) 2
line (out) 4
line (out) 5
line (out) 7
line (out) 8
""".lstrip()
    )
    assert (
        err
        == """
line (err) 0
line (err) 3
line (err) 6
line (err) 9
""".lstrip()
    )

    out, err = runner.runc([sys.executable, exe], overrdides={"HELLO": "123"})
    assert (
        out
        == """
HELLO=123
line (out) 1
line (out) 2
line (out) 4
line (out) 5
line (out) 7
line (out) 8
""".lstrip()
    )
