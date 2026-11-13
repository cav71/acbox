#!/usr/bin/env python3

"""make a release"""
# /// script
# dependencies = [
# "acbox",
# ]
# ///

import logging
import re
import subprocess
from argparse import Namespace
from pathlib import Path

import acbox.clickwrapper as cw

log = logging.getLogger(__name__)


def add_arguments(fn: cw.MainFn) -> cw.MainFn:
    fn = cw.click.argument("mode", type=cw.click.Choice(["major", "minor", "micro"]))(fn)
    fn = cw.click.option("--commit", is_flag=True)(fn)
    return fn


def get_pyproject(path: Path) -> tuple[list[tuple[int, str]], dict]:
    lines = []
    data = {}
    for index, line in enumerate(path.read_text().split("\n")):
        lines.append((index, line))
        if re.search(r"^version\s*=", line):
            data["version"] = (index, line.partition("=")[2].strip().replace('"', "").replace("'", ""))
    return lines, data


def bump(version: list[int], mode: str) -> list[int]:
    index = {
        "major": 0,
        "micro": len(version) - 1,
        "minor": 1,
    }[mode]
    result = version[:]
    result[index] += 1
    for i in range(index + 1, len(version)):
        result[i] = 0
    return result


@cw.command("fancy", add_arguments)
def main(args: Namespace) -> None:

    # first we get the local version
    pyproject = Path("pyproject.toml")
    lines, data = get_pyproject(pyproject)

    lineno, sversion = data["version"]
    version = [int(v) for v in sversion.split(".")]

    nextversion = bump(version, args.mode)
    snextversion = ".".join(str(v) for v in nextversion)

    print(f"will release '{sversion}', and move onto '{snextversion}'")

    while (ask := input("Ok to proceed? y|N ")) or True:
        if ask.upper() in {"Y", "YES"}:
            break
        elif ask.upper() in {"", "N", "NO"}:
            return

    def run(arguments: list[str | Path]) -> None:
        cmdline = [str(a) for a in arguments]
        if args.commit:
            subprocess.check_call(cmdline)
        else:
            print("dry run:", " ".join(cmdline))

    # first tagging the code
    run(["git", "tag", "-m", "release", f"v{sversion}"])

    newline = lineno, f'version = "{snextversion}"'
    print(f"| changing line @ {lineno}")
    print(f"|   {lines[lineno][1]}")
    print(f"|   {newline[1]}")
    lines[lineno] = newline

    # updating pyproject
    pyproject.write_text("\n".join(line[1] for line in lines))
    run(["git", "commit", "-m", f"release bump {sversion} -> {snextversion}", pyproject])

    # pushing it out
    run(["git", "push", "origin", f"v{sversion}"])
    run(["git", "push", "origin", "HEAD"])


if __name__ == "__main__":
    main()
