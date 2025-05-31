#!/usr/bin/env python3
# this should only use stdlib

from __future__ import annotations

import contextlib
import copy
import dataclasses as dc
import json
import os
import platform
import subprocess  # nosec B404
import sys
from enum import IntEnum, auto
from pathlib import Path
from typing import Callable


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


def indent(txt: str, pre: str, first: str | None = None) -> str:
    return (pre if first is None else first) + txt.replace("\n", "\n" + pre)


def runc(
    cmd: str | Path | list[str | Path],
    overrides: dict[str, str | int] | None = None,
    **kwargs,
) -> str | None:
    env = copy.deepcopy(os.environ)
    env.update(overrides or {})  # type: ignore[arg-type]
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


def get_installed_using_pip(python: Path | None) -> dict[str, str]:
    if not python:
        return {}
    output = runc(
        [python, "-m", "pip", "list", "--format", "json"],
        overrides={
            "PIP_NO_CACHE_DIR": "yes",
            "PIPENV_VENV_IN_PROJECT": "1",
        },
    )
    if not output:
        return {}

    result = {}
    for item in json.loads(output.strip()):
        key = item["name"].strip().lower()
        result[stripkey(key)] = item["version"]
    return result


def diffdict(
    left: dict[str, str], right: dict[str, str], skipfn: Callable[[str, str, str], bool] | None = None
) -> list[tuple[str, str, str]]:
    # diff between 2 dict
    result = []
    for key in set(left).union(right):
        if left.get(key) == right.get(key):
            continue
        values = (left.get(key) or "N/A", right.get(key) or "N/A")
        if skipfn and skipfn(key, left.get(key) or "N/A", right.get(key) or "N/A"):
            continue
        result.append((key, *values))
    return result


def report_diffdict(
    left: dict[str, str], right: dict[str, str], skipfn: Callable[[str, str, str], bool] | None = None, message: str = ""
) -> Record:
    delta = diffdict(left, right, skipfn)
    if delta:
        msg = "\n".join(f"- {', '.join(d)}" for d in delta)
        return Record(f"difference detected{message}", S.FAILED, msg)
    else:
        return Record(f"no difference detected{message}", S.OK)


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


def check_python(name: str) -> Record:
    exe = which1(name)
    if exe is None:
        return Record(f"cannot find {name}", S.FAILED)
    version = runc([name, "-V"])
    status = S.OK
    if not version:
        version = "N/A"
        status = S.WARN
    else:
        version = version.partition(" ")[2].strip()
    return Record(f"location for {name} (v. {version}): {exe}", status)


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
                # target = None
                lso.missing.append(name)
            else:
                target = (target or "").partition(" ")[0]
                lso.deps[name] = Path(target)

    if any(lso.missing for lso in result.values()):
        lines = []
        for path, lso in result.items():
            if not lso.missing:
                continue
            lines.append(f"{path} missing: {', '.join(lso.missing)}")
        return Record("missing .so files", report="\n".join(lines))

    # TODO check for libpython rpaths!
    return Record(".so files ok", S.OK)


def test_value(what, expected, found, status=S.FAILED) -> Record:
    if expected == found:
        return Record(f"found the expected value for '{what}': '{expected}'", S.OK)
    return Record(f"value expected for '{what}' is '{expected}' but found '{found}'", status)


def main() -> int:
    config = json.loads((Path(__file__).parent / "conf.json").read_text())

    report = []

    # system
    report.append(Record(f"architecture: {platform.uname().machine}"))
    report.append(Record(f"system: {platform.uname().system}"))
    report.append(Record(f"sys.platform value: {sys.platform}"))

    # python
    report.append(check_python("python"))
    report.append(check_python("python3"))

    # packages
    expected = {c["name"]: c["version"] for c in config["packages"]}
    found = get_installed_using_pip(which1("python"))

    def skipfn(_name: str, left: str, _right: str) -> bool:
        return left == "N/A"

    report.append(report_diffdict(expected, found, skipfn, " between installed packages and expected"))

    #     # packages/.so
    #     report.append(check_installed_python_packages())
    #     report.append(missing_so_files(Path("/opt/python")))

    print("= POST BUILD CHECKS =")
    print(dumps(report))
    print("= END POST BUILD CHECKS =")

    return min(int(sum(r.status == S.FAILED for r in report)), 1)


if __name__ == "__main__":
    sys.exit(main())
