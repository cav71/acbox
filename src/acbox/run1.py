from __future__ import annotations

import dataclasses as dc
import datetime
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import BinaryIO, Literal, Sequence

COLORS = {
    "blue": "\033[94m",
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "clear": "\033[0m",
}

POLL_S = 0.03

logger = logging.getLogger(__name__)


@dc.dataclass
class RunnerError(Exception):
    message: str
    cwd: Path | None
    overrides: dict[str, str] | None
    cmdline: str
    returncode: int


@dc.dataclass
class TimeoutRunnerError(RunnerError):
    pass


@dc.dataclass
class BaseFilter:
    def __call__(self, stream: BinaryIO) -> None:
        for line in iter(stream.readline, b""):
            pass


OMode = Literal["null", "capture", "display", "capture+display", "display+capture"] | BaseFilter
EMode = Literal["null", "capture", "display", "capture+display", "display+capture"] | BaseFilter
Paths = str | Path | Sequence[str | Path]


@dc.dataclass
class CaptureFilter(BaseFilter):
    encode: str | None = "utf-8"
    result: str | bytes | None = None

    def __call__(self, stream: BinaryIO) -> None:
        result = []
        for line in iter(stream.readline, b""):
            result.append(line[:-1])
        stream.close()
        if self.encode:
            self.result = b"\n".join(result).decode(self.encode)
        else:
            self.result = b"\n".join(result)


@dc.dataclass
class DisplayFilter(BaseFilter):
    color: str | None
    pre: str = "   | "
    clear: str = COLORS["clear"]
    capture: bool = False
    encode: str | None = "utf-8"
    result: str | bytes | None = None

    def __call__(self, stream: BinaryIO) -> None:
        result = []
        for rawline in iter(stream.readline, b""):
            if self.capture:
                result.append(rawline[:-1])
            line = rawline.decode("utf-8")
            if line.strip().startswith("Warning:"):
                line = line.replace("Warning:", f"{COLORS['red']}Warning:{self.clear}{self.color}")
            print(
                f"{self.pre}{self.color}{line.rstrip()}{self.clear}",
                flush=True,
                file=sys.stderr,
            )
        stream.close()
        if self.capture:
            self.result = b"\n".join(result).decode(self.encode) if self.encode else b"\n".join(result)


def mkpaths(args: Paths) -> list[str]:
    return [str(args)] if isinstance(args, (str, Path)) else [str(a) for a in args]


def runc(
    args: Paths,
    stdout: OMode = "display",
    stderr: EMode = "display",
    overrides: dict[str, str] | None = None,
    timeout: datetime.datetime | datetime.timedelta | int | float | None = None,
    **kwargs,
) -> tuple[str | bytes | None, str | bytes | None]:
    kwargs["env"] = kwargs.pop("env") if "env" in kwargs else os.environ.copy()
    kwargs["env"].update(overrides or {})
    kwargs["cwd"] = (str(v) if (v := kwargs.pop("cwd")) else None) if "cwd" in kwargs else None

    filtermaps: dict[str, BaseFilter] = {}
    for key, color in [("stdout", COLORS["blue"]), ("stderr", COLORS["yellow"])]:
        if isinstance(locals()[key], BaseFilter):
            filtermaps[key] = locals()[key]
        elif isinstance(locals()[key], str):
            flags = set(locals()[key].split("+"))
            if extra := (flags - {"capture", "display", "null"}):
                raise RuntimeError(f"cannot handle {stdout=}")
            if flags == {"capture"}:
                filtermaps[key] = CaptureFilter()
            elif flags == {"null"}:
                filtermaps[key] = BaseFilter()
            elif flags == {"display"}:
                filtermaps[key] = DisplayFilter(color, "   | ", capture=False)
            elif flags == {"capture", "display"}:
                filtermaps[key] = DisplayFilter(color, "   | ", capture=True)
        else:
            raise RuntimeError(f"cannot handle {key} with {locals()[key]}")

    with subprocess.Popen(mkpaths(args), stderr=subprocess.PIPE, stdout=subprocess.PIPE, **kwargs) as process:
        othread = threading.Thread(target=filtermaps["stdout"], args=(process.stdout,), daemon=True)
        ethread = threading.Thread(target=filtermaps["stderr"], args=(process.stderr,), daemon=True)

        expiry = None
        if timeout:
            if isinstance(timeout, datetime.datetime):
                expiry = timeout
            elif isinstance(timeout, datetime.timedelta):
                expiry = datetime.datetime.now() + timeout
            elif isinstance(timeout, (int, float)):
                expiry = datetime.datetime.now() + datetime.timedelta(seconds=float(timeout))

        started = False
        while True:
            if expiry and datetime.datetime.now() > expiry:
                process.terminate()
                break
            if not started:
                othread.start()
                ethread.start()
                started = True
            time.sleep(POLL_S)
            if process.poll() is not None:
                break

        if started:
            othread.join()
            ethread.join()

    kind = RunnerError
    if expiry and datetime.datetime.now() > expiry:
        kind = TimeoutRunnerError

    if process.returncode:
        # envs = " ".join(f'{k}="{v}"' for k, v in (overrides or {}).items())
        cmdline = subprocess.list2cmdline(mkpaths(args))
        raise kind(f"failed to execute {cmdline}", kwargs["cwd"], overrides, cmdline, process.returncode)

    return (
        getattr(filtermaps["stdout"], "result", None),
        getattr(filtermaps["stderr"], "result", None),
    )


def testing():
    from random import randint

    counter = None if len(sys.argv) < 3 else int(sys.argv[2])
    index = 0
    while (counter is None) or counter >= 0:
        code = randint(1, 2)
        out = sys.stderr if (code == 1) else sys.stdout
        print(f"{index=:04} - a message from {out} {code}", file=out)
        time.sleep(0.03)
        index += 1
        counter -= 1


if __name__ == "__main__":
    if len(sys.argv) == 1 or (mode := sys.argv[1]) not in {"run", "test"}:
        print(f"{Path(sys.argv[0]).name} run")
        sys.exit()
    if mode == "run":
        ret = runc(
            [sys.executable, __file__, "test", *sys.argv[2:]], stdout="display+capture", stderr="display+capture"
        )[1]
        print(f"{ret=}")
    elif mode == "test":
        testing()
