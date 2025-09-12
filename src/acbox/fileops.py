from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator


def which_n(exe: str | Path) -> list[Path] | None:
    candidates: list[Path] | None = None
    for srcdir in os.environ.get("PATH", "").split(os.pathsep):
        for ext in os.environ.get("PATHEXT", "").split(os.pathsep):
            path = srcdir / Path(exe).with_suffix(ext)
            if not path.exists():
                continue
            if candidates is None:
                candidates = []
            candidates.append(path)
    return candidates


def which(exe: str | Path) -> Path | None:
    candidates = which_n(exe)
    if candidates is None:
        return None
    return candidates[0]


@contextlib.contextmanager
def tmpdir(source: Path | None) -> Generator[Path, None, None]:
    wdir = source if source else Path(tempfile.mkdtemp())
    wdir.mkdir(parents=True, exist_ok=True)
    try:
        yield wdir
    finally:
        if not source:
            shutil.rmtree(wdir, ignore_errors=True)
