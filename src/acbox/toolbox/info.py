import os
import platform
import shutil
import sys
from pathlib import Path

from acbox.ureporting import Record, S, check, print_report


@check
def check_sys(group) -> list[Record]:
    return [
        Record(S.NOSTATUS, group, "executable", sys.executable),
        Record(S.NOSTATUS, group, "version", str(sys.version_info)),
    ]


@check
def check_plaform(group: str) -> list[Record]:
    return [
        Record(S.NOSTATUS, group, "arch", str(platform.architecture(sys.executable))),
        Record(S.NOSTATUS, group, "system", str(platform.uname().system)),
    ]


@check
def check_environ(group: str) -> list[Record]:
    def chunk(txt, n):
        return [txt[i : i + n] for i in range(0, len(txt), n)]

    special = {
        "PATH": lambda key, value: value.split(os.pathsep),
        "MANPATH": lambda value: value.split(os.pathsep),
        "DIRENV_DIFF": lambda key, value: chunk(value, 70),
        "DIRENV_WATCHES": lambda key, value: chunk(value, 70),
        "LS_COLORS": lambda value: chunk(value, 70),
        lambda key: key.startswith("GITHUB_"): None,
    }
    result = []
    for key, value in sorted(os.environ.items(), key=lambda k: k[0].upper()):
        if key in {"_"}:
            continue
        for keyfn, valuefn in special.items():
            if isinstance(keyfn, str) and key == keyfn:
                if callable(valuefn):
                    value = valuefn(key, value)  # type: ignore
                elif valuefn is None:
                    continue
                else:
                    value = valuefn
            if callable(keyfn) and keyfn(key):
                value = valuefn(key, value) if callable(valuefn) else valuefn  # type: ignore
        if not value:
            continue
        result.append(Record(S.NOSTATUS, group, key, value))
    return result


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
            bins = [f"found in {found}"]
            if found != str(Path(found).resolve()):
                bins = [*bins, f"({Path(found).resolve()})"]
            result.append(Record(S.NOSTATUS, group, exe, bins))
        else:
            result.append(Record(S.NOSTATUS, group, exe, "not found"))
    return result


@check
def check_envfile(group: str) -> list[Record]:
    path = Path("/etc/env.sh")
    result = []
    if path.exists():
        lines = [
            [l1.strip() for l1 in line.split("=")]
            for line in path.read_text().split("\n")
            if line.strip() and "=" in line and len(line.split("=")) == 2
        ]
        for key, value in lines:
            result.append(Record(S.NOSTATUS, group, key, value))
    else:
        result.append(Record(S.NOSTATUS, group, "not-found"))
    return result


def main() -> int:
    report = []
    report.extend(check_sys("sys"))
    report.extend(check_plaform("platform"))
    report.extend(check_environ("environ.env"))
    report.extend(check_executables("environ.exe"))
    report.extend(check_envfile("envfile"))
    return print_report(report)


if __name__ == "__main__":
    sys.exit(main())
