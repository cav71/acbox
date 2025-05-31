#!/usr/bin/env python3
# this should only use stdlib

from __future__ import annotations

import contextlib
import dataclasses as dc
import json
import os
import platform
import re
import subprocess  # nosec B404
import sys
from enum import IntEnum, auto
from pathlib import Path


class S(IntEnum):
    OK = auto()
    FAILED = auto()
    WARN = auto()
    NOSTATUS = auto()


@dc.dataclass
class Record:
    short: str
    status: S = S.NOSTATUS
    report: str = ""


def runc(
    cmd: str | Path | list[str | Path],
    overrides: dict[str, str | int] | None = None,
    **kwargs,
) -> str | None:
    env = os.environ.copy()
    env.update(overrides or {})
    cmd = [str(cmd)] if isinstance(cmd, (Path, str)) else [str(c) for c in cmd]
    if kwargs.pop("quiet", None):
        kwargs["stderr"] = subprocess.DEVNULL
    with contextlib.suppress(subprocess.CalledProcessError):
        return subprocess.check_output(cmd, encoding="utf-8", env=env, **kwargs)  # nosec B603
    return None


def which(exe: str | Path) -> list[Path] | None:
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


def which1(exe: str | Path) -> Path | None:
    candidates = which(exe)
    if candidates is None:
        return None
    return candidates[0]


def stripkey(txt: str) -> str:
    # eg. celery[pytest] -> celery
    if "[" in txt:
        txt = txt.partition("[")[0]
    return txt.strip().lower().replace("_", "-")


def get_installed_using_pip(workdir: Path) -> dict[str, str]:
    output = runc(
        ["pipenv", "run", "pip", "list", "--format", "json"],
        overrides={
            "PIP_NO_CACHE_DIR": "yes",
            "PIPENV_VENV_IN_PROJECT": "1",
        },
        cwd=workdir,
    )

    result = {}
    for item in json.loads(output.strip()):
        key = item["name"].strip().lower()
        result[stripkey(key)] = item["version"]
    return result


def get_installed_using_pipenv(workdir: Path) -> dict[str, str]:
    output = runc(["pipenv", "requirements"], cwd=workdir).strip()
    packages = {}
    for line in output.split("\n"):
        # eg. lines like '-i url'
        if "-i " in line:
            continue

        values = line
        if ";" in line:
            values = line.partition(";")[0]
        values = values.split("==")  # in requirements only ==

        # eg.
        if line.count("@") == 2:
            # instructor @ git+https://github.com/narmi/instructor.git@2b602c53679c5d6bce2048828df92a68359627dd
            values = line.split("@")[::2]
        elif match := (re.compile(r"(https|http|file)://(?P<url>[^ ;]+)").search(line)):
            # https://some.url/path/csv2ofx-some-weird--0.30.1-py2.py3-none-any.whl ; python_version >= '3.9'
            items = match.group("url").rpartition("/")[2].split("-")[:-3]
            values = "-".join(items[:-1]), items[-1]

        name, version = values
        packages[stripkey(name)] = version

    return packages


def diffdict(left: dict[str, str], right: dict[str, str], skip: dict[str, tuple[str, str] | None]) -> list[str, str, str]:
    # diff between 2 dict
    result = []
    for key in set(left).union(right):
        if left.get(key) == right.get(key):
            continue
        values = (left.get(key) or "N/A", right.get(key) or "N/A")
        if key in skip and ((not skip[key]) or (skip[key] == values)):
            continue
        result.append((key, *values))
    return result


def indent(txt: str, pre: str, first: str | None = None) -> str:
    return (pre if first is None else first) + txt.replace("\n", "\n" + pre)


def dumps(report: list[Record]) -> str:
    result = []

    def color(status: S) -> str:
        reset = "\033[0m"
        return {
            S.OK: f"\033[42m+{reset}",
            S.FAILED: f"\033[41mx{reset}",
            S.WARN: f"\033[43m!{reset}",
            S.NOSTATUS: ".",
        }[status]

    for record in report:
        result.append(f"{color(record.status)} {record.short}")
        if record.report:
            result.append(indent(record.report, " " * 2))
    return "\n".join(result)


def check_value(what, expected, found, status=S.FAILED) -> Record:
    if expected == found:
        return Record(f"found the expected value for '{what}': '{expected}'", S.OK)
    return Record(f"value expected for '{what}' is '{expected}' but found '{found}'", status)


def missing_so_files(root: Path):
    @dc.dataclass
    class LSO:
        missing: list[str] = dc.field(default_factory=list)
        deps: dict[str, Path] = dc.field(default_factory=dict)

    result = {}
    for path in root.rglob("*"):
        if not (path.name.endswith(".so") or os.access(path, os.X_OK)):
            continue
        paths = runc(["ldd", path], quiet=True)
        if paths is None:
            continue
        result[path] = lso = LSO()

        for line in paths.split("\n"):
            if "=>" not in line:
                continue
            name, target = [p.strip() for p in line.split("=>")]
            if target == "not found":
                target = None
                lso.missing.append(name)
            else:
                target = target.partition(" ")[0]
                lso.deps[name] = Path(target)

    if any(lso.missing for lso in result.values()):
        lines = []
        for path, lso in result.items():
            if not lso.missing:
                continue
            lines.append(f"{path} missing: {', '.join(lso.missing)}")
        return Record("missing .so files", "\n".join(lines))

    # TODO check for libpython rpaths!
    return Record(".so files ok", S.OK)


def main() -> int:
    report = []

    report.append(check_value("architecture", "x86_64", platform.uname().machine, S.WARN))
    report.append(check_value("system", "Linux", platform.uname().system))

    # python
    found = which("python")
    report.append(Record(f"where's python: {found}", S.OK if found else S.WARN))

    #     found = runc(["pipenv", "run", "which", "python"], cwd=WORKDIR).strip()
    #     report.append(Record(f"where's the python detected by pipenv: {found}"))
    #
    #     # python3
    #     found = runc(["which", "python3"]).strip()
    #     report.append(Record(f"where's python3: {found}"))
    #     found = runc(["python3", "-V"]).strip()
    #     report.append(Record(f"which python3 version: {found}"))
    #
    #     found = runc(["pipenv", "run", "which", "python3"], cwd=WORKDIR).strip()
    #     report.append(Record(f"where's the python3 detected by pipenv: {found}"))
    #     found = runc(["pipenv", "run", "python3", "-V"], cwd=WORKDIR).strip()
    #     report.append(Record(f"which python version detected by pipenv: {found}"))
    #
    #     # TODO verify this, for what imports
    #     found = (
    #         runc(
    #             ["pipenv", "run", "python", "-c", "import narmi;print(narmi.__file__)"],
    #             cwd=WORKDIR,
    #         )
    #         or ""
    #     ).strip()
    #     report.append(
    #         Record(f"narmi source '{found or 'not-found'}'", S.OK if found else S.FAILED)
    #     )
    #
    #     # packages/.so
    #     report.append(check_installed_python_packages())
    #     report.append(missing_so_files(Path("/opt/python")))

    print("= POST BUILD CHECKS =")
    print(dumps(report))
    print("= END POST BUILD CHECKS =")

    return min(int(sum(r.status == S.FAILED for r in report)), 1)


if __name__ == "__main__":
    sys.exit(main())
