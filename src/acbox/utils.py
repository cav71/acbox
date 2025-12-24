from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen


def loadmod(path: Path | str | StringIO) -> ModuleType:
    txt = None
    if isinstance(path, StringIO):
        txt = path.getvalue()
        path = "unknown"
    elif (parsed := urlparse(str(path))).scheme in {"http", "https"}:
        txt = str(urlopen(str(path)).read(), encoding="utf-8")
    elif parsed.scheme in {"file"}:
        txt = Path(parsed.netloc).read_text()

    if txt is not None:
        mod = ModuleType(str(path).rpartition("/")[2])
        exec(txt, mod.__dict__)
        return mod

    spec = spec_from_file_location(Path(path).name, Path(path))
    module = module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore
    return module


class NA:
    pass


def diffdict(
    left: dict[str, Any], right: dict[str, Any], exclude: list[str] | None = None, na: str | type[NA] = NA
) -> dict[str, tuple[Any, Any]]:
    result = {}
    for key in sorted(set(left) | set(right)):
        if exclude and key in exclude:
            continue
        if key not in left:
            result[key] = (na, right[key])
        elif key not in right:
            result[key] = (left[key], na)
        elif left[key] != right[key]:
            result[key] = (left[key], right[key])
    return result
