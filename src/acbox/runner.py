from __future__ import annotations

import contextlib
import dataclasses as dc
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Generator

from .run1 import EMode, OMode, Paths, mkpaths, runc

logger = logging.getLogger(__name__)


@dc.dataclass
class Runner:
    verbose: bool
    dryrun: bool | None = None
    exe: Paths | None = None
    cwd: Path | None = None
    overrides: dict[str, str] | None = None
    log: logging.Logger | None = None

    @staticmethod
    @contextlib.contextmanager
    def tmpdir(source: Path | None = None) -> Generator[Path, None, None]:
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
        overrides: dict[str, str] | None = None,
        log: logging.Logger | None = None,
    ) -> str | bytes | None:
        # capture/verbose are interacting to control how the stdout is handled
        check = (capture, self.verbose if verbose is None else verbose)
        stdout: OMode = "null"
        if check == (True, False):
            stdout = "capture"
        elif check == (True, True):
            stdout = "capture+display"
        elif check == (False, True):
            stdout = "display"
        elif check == (False, False):
            stdout = "null"
        else:
            raise RuntimeError(f"un-handled value {check=}")
        stderr: EMode = "display" if self.verbose else "null"

        dryrun = self.dryrun if dryrun is None else dryrun
        if "capture" in stdout and dryrun:
            raise RuntimeError("cannot dryrun and caputure")

        cwd = cwd or self.cwd
        overrides = overrides or self.overrides
        log = log or self.log or logger

        fullargs = mkpaths(args)
        if self.exe:
            fullargs = [*mkpaths(self.exe), *fullargs]

        log.debug("%srun: %s", "(dry-run) " if dryrun else "", " ".join(fullargs))
        if dryrun:
            return None
        return runc(fullargs, stdout=stdout, stderr=stderr, overrides=overrides, cwd=cwd)


if __name__ == "__main__":
    runner = Runner(True)
    y = runner(["ls", "-l"], capture=False, verbose=True)
    print(y)

    # --git-dir=$dest/.git --work-tree $dest
    runner = Runner(True, exe=["git", "--git-dir", "{workdir}/.git"])
    runner("status")
