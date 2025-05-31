from __future__ import annotations

from pathlib import Path
from types import ModuleType


def loadmod(path: Path | str) -> ModuleType:
    from importlib import util
    from types import ModuleType
    from urllib.parse import urlparse
    from urllib.request import urlopen

    if urlparse(str(path)).scheme in {"http", "https"}:
        urltxt = str(urlopen(str(path)).read(), encoding="utf-8")
        mod = ModuleType(str(path).rpartition("/")[2])
        exec(urltxt, mod.__dict__)
        return mod

    spec = util.spec_from_file_location(Path(path).name, Path(path))
    module = util.module_from_spec(spec)  # type: ignore
    spec.loader.exec_module(module)  # type: ignore
    return module
