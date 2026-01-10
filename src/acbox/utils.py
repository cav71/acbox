from __future__ import annotations

import random
import string
import sys
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen


def loadmod(path: Path | str | StringIO, variables: dict[str, Any] | None = None, name: str = "") -> ModuleType:
    random_name = "".join(random.choices(string.ascii_lowercase, k=5))
    random_name = f"loadmod.{random_name}"

    txt = None
    if isinstance(path, Path):
        txt = path.read_text()
    elif isinstance(path, StringIO):
        txt = path.getvalue()
        path = "<string>"
    elif (parsed := urlparse(str(path))).scheme in {"http", "https"}:
        txt = str(urlopen(str(path)).read(), encoding="utf-8")
        path = f"<string {path}>"
    elif parsed.scheme in {"file"}:
        txt = Path(parsed.netloc).read_text()
        path = parsed.netloc
    else:
        raise ValueError(f"unsupported path type: {path}")

    mod = ModuleType(name)
    mod.__dict__.update(variables or {})
    mod.__dict__["__name__"] = name or random_name
    mod.__file__ = str(path)
    code_obj = compile(txt, filename=str(path), mode="exec")
    sys.modules[name] = mod
    exec(code_obj, mod.__dict__)
    return mod

    # spec = spec_from_file_location(Path(path).name, Path(path))
    # module = module_from_spec(spec)  # type: ignore
    # spec.loader.exec_module(module)  # type: ignore
    # return module


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
