from __future__ import annotations

import dataclasses as dc
import json
import logging
from pathlib import Path
from typing import Any, Sequence

from . import utils

logger = logging.getLogger(__name__)

Paths = str | Path | Sequence[str | Path]


def makepaths(args: Paths) -> list[Path]:
    if isinstance(args, (str, Path)):
        return [Path(args)]
    return [Path(a) for a in args]


@dc.dataclass
class LoaderBase:
    paths: list[Path] | None = None

    def __post_init__(self):
        self.paths = [Path(p).expanduser() for p in (self.paths or [])]

    def lookup(self, name: Path | str, abort: bool = False) -> Path | None:
        for item in self.paths or [Path.cwd()]:
            if (found := (item / name)).exists():
                return found
        if abort:
            raise FileNotFoundError(2, "cannot lookup name", name, self.paths)
        return None

    def load(self, name: Path | str, mode: str | None = None, abort: bool = True) -> Any:
        if not (path := self.lookup(name, abort=abort)):
            return None
        mode = mode or path.suffix.strip(".").lower()

        if mode == "json":
            return json.loads(path.read_text())
        elif mode == "text":
            return path.read_text()
        elif mode in {"binary", "raw", "bytes"}:
            return path.read_bytes()
        elif mode == "mod":
            return utils.loadmod(path)
        elif mode in {"yaml", "yml"}:
            from yaml import safe_load

            return safe_load(self.load(path.absolute(), "text"))

        raise TypeError(f"cannot find type ({mode}) for {path}")


acloader = LoaderBase(paths=[Path(__file__).parent / "shared"])
