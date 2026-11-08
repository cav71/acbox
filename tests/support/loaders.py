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
    import tomli as tomllib  # type: ignore[import-not-found]

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

        def lookup(self, path: Path | str) -> Path:
            candidates = [
                self.root / self.name / path,
                self.root / path,
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
            raise FileNotFoundError(f"cannot find {path}", candidates)

        def load(self, path: Path, mode: str | None = None) -> Any:
            source = self.lookup(path)
            mode = mode or source.suffix.strip(".")
            if mode == "json":
                return json.loads(source.read_text())
            elif mode == "text":
                return source.read_text()
            elif mode == "mod":
                return loadmod(source)
            elif mode == "toml":
                return tomllib.loads(source.read_text())
            raise RuntimeError(f"mode '{mode}' not supported")

    yield Resolver(DATADIR, request.module.__name__)
