import contextlib
import dataclasses as dc
import logging
import os
import shutil
import subprocess
import sys
import tempfile
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

logger = logging.getLogger(__name__)


class RunnerError(Exception):
    pass


@dc.dataclass
class BaseFilter:
    def __call__(self, stream: BinaryIO) -> None:
        for line in iter(stream.readline, b""):
            pass


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


OMode = Literal["capture", "null", "display", "capture+display"] | BaseFilter
EMode = Literal["null", "display"] | BaseFilter
Paths = str | Path | Sequence[str | Path]


def mkpaths(args: Paths) -> list[str]:
    return [str(args)] if isinstance(args, (str, Path)) else [str(a) for a in args]


def runc(
    args: Paths,
    stdout: OMode = "display",
    stderr: EMode = "display",
    overrides: dict[str, str] | None = None,
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
        othread.start()
        ethread.start()
        while process.poll() is not None:
            time.sleep(0.05)
        othread.join()
        ethread.join()

    if process.returncode:
        envs = " ".join(f'{k}="{v}"' for k, v in (overrides or {}).items())
        cmdline = subprocess.list2cmdline(mkpaths(args))
        raise RunnerError(f"failed to execute in cwd={kwargs['cwd']} ==> {envs} {cmdline}")
    return ofiltermap.result if hasattr(ofiltermap, "result") else None


@dc.dataclass
class Runner:
    verbose: bool
    dryrun: bool | None = None
    exe: Paths | None = None
    cwd: Path | None = None
    log: logging.Logger | None = None

    @staticmethod
    @contextlib.contextmanager
    def tmpdir(source: Path | None):
        wdir = source if source else Path(tempfile.mkdtemp())
        wdir.mkdir(parents=True, exist_ok=True)
        try:
            yield wdir
        finally:
            if not source:
                shutil.rmtree(wdir, ignore_errors=True)

    def __call__(
        self,
        args: Paths,
        capture: bool = False,
        verbose: bool | None = None,
        dryrun: bool | None = None,
        cwd: Path | str | bool | None = None,
        log: logging.Logger | None = None,
    ):
        log = log or self.log or logger
        dryrun = self.dryrun if dryrun is None else dryrun
        cwd = cwd or self.cwd
        display: EMode = "display" if self.verbose else "null"

        check = (capture, self.verbose if verbose is None else verbose)
        mode: OMode = "null"
        if check == (True, False):
            mode = "capture"
        elif check == (True, True):
            mode = "capture+display"
        elif check == (False, True):
            mode = "display"
        elif check == (False, False):
            mode = "null"
        else:
            raise RuntimeError(f"un-handled value {check=}")
        if "capture" in mode and dryrun:
            raise RuntimeError("cannot dryrun and caputure")
        fullargs = mkpaths(args)
        if self.exe:
            variables = {"cwd": cwd}
            fullargs = [*mkpaths(self.exe), *fullargs]
            fullargs = [a.format(**variables) for a in fullargs]

        log.debug("%srun: %s", "(dry-run) " if dryrun else "", " ".join(fullargs))
        return runc(fullargs, stdout=mode, stderr=display, cwd=cwd)


if __name__ == "__main__":
    x = runc(["ls", "-l"], "capture", "display")
    print(x)

    runner = Runner(True)
    y = runner(["ls", "-l"], capture=False, verbose=True)
    print(y)

    # --git-dir=$dest/.git --work-tree $dest
    runner = Runner(True, exe=["git", "--git-dir", "{workdir}/.git"])
    runner("status")
