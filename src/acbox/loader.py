from __future__ import annotations

import dataclasses as dc
import logging
from pathlib import Path
from typing import Any, Literal, Sequence

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

    def lookup(self, name: Path | str) -> Path | None:
        for item in self.paths or [Path.cwd()]:
            if (found := (item / name)).exists():
                return found
        return None

    def load(self, name: Path | str, mode: Literal["auto", "binary", "raw", "text"] = "auto") -> Any:
        if not (path := self.lookup(name)):
            raise FileNotFoundError(2, "cannot lookup name", name)

        if mode in {"binary", "raw"}:
            return path.read_bytes()
        elif mode == "text":
            return path.read_text()

        kind = path.suffix
        if kind.upper() in {".JSON"}:
            from json import loads

            return loads(self.load(path.absolute(), "text"))
        elif kind.upper() in {".YAML", ".YML"}:
            from yaml import safe_load

            return safe_load(self.load(path.absolute(), "text"))
        else:
            raise TypeError(f"cannot find type ({kind}) for {path}")
        return None
