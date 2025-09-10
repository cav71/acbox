import os
import platform
import sys
import shutil
import dataclasses as dc
from pathlib import Path
from tooling.ureporting import check, print_report, Record, S
from typing import Callable

@dc.dataclass
class skipfn:
    callable: Callable
    def __call__(self, key, value):
        return self.callable(key, value) 


def githubs(key, value):
    return key.startswith("GITHUB_")


@check
def check_sys(group) -> list[Record]:
    return [
        Record(S.NOSTATUS, group, "executable", sys.executable),
        Record(S.NOSTATUS, group, "version", sys.version_info),
    ]


@check
def check_environ(group) -> list[Record]:
    def chunk(txt, n):
        return [txt[i:i+n] for i in range(0, len(txt),n)]

    exclude = [
        skipfn(githubs)
    ]
    special = {
        "PATH": lambda value: value.split(os.pathsep),
        "MANPATH": lambda value: value.split(os.pathsep),
        "DIRENV_DIFF": lambda value: chunk(value, 70),
        "DIRENV_WATCHES": lambda value: chunk(value, 70),
    }
    result = []
    for key, value in sorted(os.environ.items(), key=lambda k: k[0].upper()):
        if any(fn(key, value) for fn in exclude):
            continue
        if key in {"_"}:
            continue
        fn = special.get(key, lambda value: value)
        result.append(Record(S.NOSTATUS, group, key, fn(value))) 
    return result


@check
def check_plaform(group: str) -> list[Record]:
    return [
        Record(S.NOSTATUS, group, "arch", platform.architecture(sys.executable)),
        Record(S.NOSTATUS, group, "system", platform.uname().system),
    ]


@check
def check_executables(group: str) -> list[Record]:
    exes = [
        "git",
        "python",
        "python3",
        "pip",
        "pip3",
    ]
    result = []
    for exe in exes:
        if found := shutil.which(exe):
            bins = f"found in {found}"
            if found != str(Path(found).resolve()):
                bins = [bins, f"({Path(found).resolve()})"]
            result.append(Record(S.NOSTATUS, group, exe, bins))
        else:
            result.append(Record(S.NOSTATUS, group, exe, f"not found"))
    return result


@check
def check_envfile(group: str) -> list[Record]:
    path = Path("/etc/env.sh")
    result = []
    if path.exists():
        lines = [
            [l.strip() for l in line.split("=")] 
            for line in path.read_text().split("\n") 
            if line.strip() and "=" in line and len(line.split("=")) == 2
        ]
        for key, value in lines:
            result.append(Record(S.NOSTATUS, group, key, value))
    else:
        result.append(Record(S.NOSTATUS, group, "not-found")) 
    return result


if __name__ == "__main__":
    report = []
    report.extend(check_sys("sys"))
    report.extend(check_plaform("platform"))
    report.extend(check_environ("environ.env"))
    report.extend(check_executables("environ.exe"))
    report.extend(check_envfile("envfile"))
    sys.exit(print_report(report))
