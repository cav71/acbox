import dataclasses as dc
import os
import sys
import time
from typing import Any, BinaryIO

import pytest

from acbox import run1


@dc.dataclass
class BufferFilter(run1.BaseFilter):
    buffer: list[str] = dc.field(default_factory=list)
    exception: Any = ""

    def __call__(self, stream: BinaryIO) -> None:
        try:
            for buffer in iter(stream.readline, b""):
                line = buffer.decode("utf-8")
                if line.endswith(os.linesep):
                    line = line[: -len(os.linesep)]
                self.buffer.append(line)
        except Exception as exc:
            self.exception = exc


@pytest.fixture(scope="function")
def filters():
    @dc.dataclass
    class Filters:
        stdout: BufferFilter  # type: ignore
        stderr: BufferFilter  # type: ignore

        def reset(self):
            self.stdout.buffer = []
            self.stderr.buffer = []

    yield Filters(stdout=BufferFilter(), stderr=BufferFilter())


def test_new_filter(resolver, filters):
    """simply capture the stdout / stderr"""
    cmd = [sys.executable, resolver.lookup("simple-script.py")]

    run1.runc(cmd, **filters.__dict__)
    assert ["1, got 'first message' (<stdout>)"] == filters.stdout.buffer
    assert ["2, got 'second message' (<stderr>)"] == filters.stderr.buffer

    filters.reset()
    run1.runc(cmd, overrides={"VALUE": "123"}, **filters.__dict__)
    assert ["1, got 'first message' (<stdout>)", "3, got 'received [123]' (<stdout>)"] == filters.stdout.buffer
    assert ["2, got 'second message' (<stderr>)", "4, got 'received [123]' (<stderr>)"] == filters.stderr.buffer


def test_new_filter_with_error(resolver, filters):
    cmd = [sys.executable, resolver.lookup("simple-script.py")]
    with pytest.raises(run1.RunnerError) as exc:
        run1.runc(cmd, overrides={"ABORT": "33"}, **filters.__dict__)

    assert ["2, got 'second message' (<stderr>)", "4, got 'aborting with 33' (<stderr>)"] == filters.stderr.buffer
    assert ["1, got 'first message' (<stdout>)", "3, got 'aborting with 33' (<stdout>)"] == filters.stdout.buffer

    assert None is exc.value.cwd
    assert {"ABORT": "33"} == exc.value.overrides
    assert " ".join(str(c) for c in cmd) == exc.value.cmdline
    assert 33 == exc.value.returncode


def test_wait_and_timeout(resolver, filters):
    cmd = [sys.executable, resolver.lookup("simple-script.py")]

    t0 = time.monotonic()
    run1.runc(cmd, overrides={"WAIT": "0.5"}, **filters.__dict__)
    delta = time.monotonic() - t0
    assert delta > 0.5
    assert [
        "1, got 'first message' (<stdout>)",
        "3, got 'waiting 0.5s ..' (<stdout>)",
        "5, got 'done waiting 0.5s' (<stdout>)",
    ] == filters.stdout.buffer
    assert [
        "2, got 'second message' (<stderr>)",
        "4, got 'waiting 0.5s ..' (<stderr>)",
        "6, got 'done waiting 0.5s' (<stderr>)",
    ] == filters.stderr.buffer

    filters.reset()
    with pytest.raises(run1.TimeoutRunnerError) as exc:
        run1.runc(cmd, overrides={"WAIT": "100"}, timeout=0.5, **filters.__dict__)
    assert exc.value.returncode
    assert None is exc.value.cwd
    assert {"WAIT": "100"} == exc.value.overrides
    assert " ".join(str(c) for c in cmd) == exc.value.cmdline
