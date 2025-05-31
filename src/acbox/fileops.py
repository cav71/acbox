from __future__ import annotations

import os
from pathlib import Path


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
