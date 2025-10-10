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


OMode = Literal["capture", "null", "display", "capture+display"] | BaseFilter
EMode = Literal["null", "display"] | BaseFilter
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
) -> str | bytes | None:
    kwargs["env"] = kwargs.pop("env") if "env" in kwargs else os.environ.copy()
    kwargs["env"].update(overrides or {})
    kwargs["cwd"] = (str(v) if (v := kwargs.pop("cwd")) else None) if "cwd" in kwargs else None

    with subprocess.Popen(mkpaths(args), stderr=subprocess.PIPE, stdout=subprocess.PIPE, **kwargs) as process:
        if stdout == "capture":
            ofiltermap: BaseFilter = CaptureFilter()
        elif stdout == "null":
            ofiltermap = BaseFilter()
        elif stdout == "display":
            ofiltermap = DisplayFilter(COLORS["blue"], "   | ")
        elif stdout == "capture+display":
            ofiltermap = DisplayFilter(COLORS["blue"], "   | ", capture=True)
        elif isinstance(stdout, BaseFilter):
            ofiltermap = stdout
        else:
            raise RuntimeError(f"unsupported type in {stdout=}")
        othread = threading.Thread(target=ofiltermap, args=(process.stdout,), daemon=True)

        if stderr == "null":
            efiltermap: BaseFilter = BaseFilter()
        elif stderr == "display":
            efiltermap = DisplayFilter(COLORS["green"], "   | ")
        elif isinstance(stderr, BaseFilter):
            efiltermap = stderr
        else:
            raise RuntimeError(f"unsupported type in {stderr=}")
        ethread = threading.Thread(
            target=efiltermap,
            args=(process.stderr,),
            daemon=True,
        )
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
    return ofiltermap.result if hasattr(ofiltermap, "result") else None


if __name__ == "__main__":
    x = runc(["ls", "-l"], "capture", "display")
    print(x)
