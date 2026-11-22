from __future__ import annotations

import dataclasses as dc
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found, unused-ignore]

import pytest

DATADIR = Path(__file__).parent.parent / "data"


def loadmod(path: Path | str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(Path(path).name, Path(path))
    module = importlib.util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore
    return module


@pytest.fixture(scope="function")
def resolver(request):
    """return a resolver object to lookup for test data

    Example:
        def test_me(resolver):
            print(resolver.lookup("a/b/c")) -> tests/data/a/b/c
    """

    @dc.dataclass
    class Resolver:
        root: Path  # type: ignore[annotation-unchecked]
        name: str  # type: ignore[annotation-unchecked]

        def lookup(self, name: Path | str, abort: bool = True) -> Path | None:
            # lookup:
            #   tests/data/test_abc/path
            #   tests/data/abc/path
            #   test/data/path
            path = Path(name)
            candidates = [
                self.root / self.name / path,
            ]
            if self.name.startswith("test_"):
                candidates.append(self.root / self.name[len("test_") :] / path)
            candidates.append(self.root / path)

            for candidate in candidates:
                if candidate.exists():
                    return candidate
            if abort:
                raise FileNotFoundError(f"cannot find {path}", candidates)
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
                return loadmod(path)
            elif mode in {"yaml", "yml"}:
                from yaml import safe_load

                return safe_load(self.load(path.absolute(), "text"))
            elif mode == "toml":
                return tomllib.loads(path.read_text())

            raise TypeError(f"cannot find type ({mode}) for {path}")

    yield Resolver(DATADIR, request.module.__name__)
