#!/usr/bin/env python3
# this should only use stdlib

from __future__ import annotations

import os
import platform
import shutil
import sys
from pathlib import Path

from acbox.ureporting import Record, S, check, print_report

# def get_installed_using_pip(python: Path | None) -> dict[str, str]:
#     if not python:
#         return {}
#     output = runc(
#         [python, "-m", "pip", "list", "--format", "json"],
#         overrides={
#             "PIP_NO_CACHE_DIR": "yes",
#             "PIPENV_VENV_IN_PROJECT": "1",
#         },
#     )
#     if not output:
#         return {}
#
#     result = {}
#     for item in json.loads(output.strip()):
#         key = item["name"].strip().lower()
#         result[stripkey(key)] = item["version"]
#     return result


# def missing_so_files(root: Path):
#     @dc.dataclass
#     class LSO:
#         missing: list[str] = dc.field(default_factory=list)
#         deps: dict[str, Path] = dc.field(default_factory=dict)
#
#     result = {}
#     for path in root.rglob("*"):
#         if not (path.name.endswith(".so") or os.access(path, os.X_OK)):
#             continue
#         paths = runc(["ldd", path], quiet=True)
#         if paths is None:
#             continue
#         result[path] = lso = LSO()
#
#         for line in paths.split("\n"):
#             if "=>" not in line:
#                 continue
#             name, target = [p.strip() for p in line.split("=>")]
#             if target == "not found":
#                 # target = None
#                 lso.missing.append(name)
#             else:
#                 target = (target or "").partition(" ")[0]
#                 lso.deps[name] = Path(target)
#
#     if any(lso.missing for lso in result.values()):
#         lines = []
#         for path, lso in result.items():
#             if not lso.missing:
#                 continue
#             lines.append(f"{path} missing: {', '.join(lso.missing)}")
#         return Record("missing .so files", report="\n".join(lines))
#
#     # TODO check for libpython rpaths!
#     return Record(".so files ok", S.OK)


def test_value(what, expected, found, status=S.FAILED) -> Record:
    if expected == found:
        return Record(f"found the expected value for '{what}': '{expected}'", S.OK)
    return Record(f"value expected for '{what}' is '{expected}' but found '{found}'", status)


@check
def system():
    result = [
        Record(S.NOSTATUS, "system", "architecture", platform.uname().machine),
        Record(S.NOSTATUS, "system", "system", platform.uname().system),
        Record(S.NOSTATUS, "system", "sys.platform", sys.platform),
        Record(S.NOSTATUS, "system", "sys.executable", sys.executable),
        Record(S.NOSTATUS, "system", "sys.version", sys.version),
    ]

    return result


@check
def executables():
    result = []
    exes = [
        "git",
        "python",
        "python3",
        "ruff",
        "mypy",
        "uv",
        "pip",
        "pip3",
    ]
    for exe in exes:
        found = shutil.which(exe)
        message = f"found {found}" if found else "not-found"
        result.append(Record(S.NOSTATUS, "executable", exe, message))

    for exe in ["python", "python3", "pip", "pip3"]:
        target = Path(".venv") / "bin" / exe
        found = None
        for ext in ["", ".exe"]:
            test = target.with_suffix(ext)
            if test.exists():
                found = str(test)
                break
        message = f"found {found}" if found else "not-found"
        result.append(Record(S.NOSTATUS, "executable", str(target), message))
    return result


@check
def env_variables():
    return Record(S.NOSTATUS, "environ", "PATH", os.environ["PATH"].split(os.pathsep))


def main() -> int:
    report = []
    report.extend(system())
    report.extend(executables())
    report.extend(env_variables())
    ret = print_report(report)
    print(f"Final status -> {ret}")
    return ret

    # packages
    # expected = {c["name"]: c["version"] for c in config["packages"]}
    # found = get_installed_using_pip(which1("python"))

    # def skipfn(name: str, left: str, _right: str) -> bool:
    #     return left == "N/A"

    # report.append(report_diffdict(expected, found, skipfn, " between installed packages and expected"))

    # # packages/.so
    # report.append(check_installed_python_packages())
    # report.append(missing_so_files(Path("/opt/python")))


if __name__ == "__main__":
    sys.exit(main())
