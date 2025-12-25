from __future__ import annotations

import dataclasses as dc
import functools
import sys
from enum import IntEnum, auto
from pathlib import Path
from typing import Sequence, TextIO


class S(IntEnum):
    OK = auto()
    FAILED = auto()
    WARN = auto()
    NOSTATUS = auto()


@dc.dataclass
class Record:
    status: S  # the status for teh record
    group: str  # group all records with the same group in output
    key: str  # unique key inside a group
    report: str | list[str] = ""


@dc.dataclass
class ColorText:
    message: str
    status: S

    def __format__(self, width):
        reset = "\033[0m"
        message = self.message
        msg = {
            S.OK: f"\033[42m{message}{reset}",
            S.FAILED: f"\033[41m{message}{reset}",
            S.WARN: f"\033[43;30m{message}{reset}",
            S.NOSTATUS: f"{message}",
        }[self.status]
        return msg + " " * (int(width or len(self.message)) - len(self.message))


def indent(txt: str, pre: str, first: str | None = None) -> str:
    return (pre if first is None else first) + txt.replace("\n", "\n" + pre)


def dumps(report: list[Record], sorted_groups: bool = True) -> str:
    def resolve(states):
        if S.FAILED in states:
            status = S.FAILED
        elif S.WARN in states:
            status = S.WARN
        elif S.OK in states:
            status = S.OK
        else:
            status = S.NOSTATUS
        return status

    def color(status: S, fall=".") -> ColorText:
        message = {
            S.OK: "+",
            S.FAILED: "x",
            S.WARN: "!",
            S.NOSTATUS: ".",
        }[status]
        return ColorText(message, status)

    def colorize(message: str, status: S) -> ColorText:
        return ColorText(message, status)

    pre = " " * 3
    result = []

    width = max(len(record.key) for record in report)

    for group in list({r.group: 1 for r in report}):
        records = [r for r in report if r.group == group]
        status = resolve(set(record.status for record in records))
        result.append(f"{color(status)} {group}")
        start = " " * 4 + " " * width
        for record in records:
            if record.group != group:
                continue
            if isinstance(record.report, str):
                message = record.report
            elif isinstance(record.report, list):
                message = indent("\n".join(record.report), pre=start).lstrip()
            else:
                raise RuntimeError("unable to handle type", type(record.report))
            result.append(f"{pre}{colorize(record.key, record.status):{width}} {message}")

    return "\n".join(result)


def print_report(report: list[Record], sorted_groups: bool = True, file: TextIO = sys.stdout) -> int:
    errors = sum(r.status == S.FAILED for r in report)
    warnings = sum(r.status == S.WARN for r in report)
    print(dumps(report, sorted_groups), file=file)
    if errors:
        t = ColorText("FAILED", S.FAILED)
        print(f"{t} found {errors} errors, and {warnings} warnings", file=file)
    elif warnings:
        t = ColorText("WARN", S.WARN)
        print(f"{t} found {warnings} warnings", file=file)
    else:
        t = ColorText("OK", S.OK)
        print(f"{t}", file=file)
    return min(int(sum(r.status == S.FAILED for r in report)), 1)


def check(fn):
    @functools.wraps(fn)
    def _fn(*args, **kwargs):
        result = fn(*args, **kwargs)
        return result if isinstance(result, list) else [result]

    _fn._is_check = True
    return _fn


def load_external_checks(paths: Sequence[str | Path]) -> list[Record]:
    from acbox.utils import loadmod

    result = []
    for path in paths:
        mod = loadmod(Path(path))
        for name in dir(mod):
            fn = getattr(mod, name)
            if not (callable(fn) and getattr(fn, "_is_check", False)):
                continue
            result.extend(fn())
    return result


if __name__ == "__main__":
    report = []
    report.append(Record(S.NOSTATUS, "group-0", "key-0", "message"))
    report.append(Record(S.OK, "group-0", "key-2", "message-2"))
    report.append(Record(S.FAILED, "group-0", "key-3", "message-3"))
    report.append(Record(S.WARN, "group-0", "key-4", "message-4"))
    report.append(Record(S.NOSTATUS, "group-1", "key-0", "message"))
    report.append(Record(S.OK, "group-1", "key-2", "message-2"))
    report.append(Record(S.OK, "group-1", "key-3", "message-3"))
    report.append(Record(S.WARN, "group-1", "key-4", "message-4"))
    ret = print_report(report)
    print(f"Final status -> {ret}")
