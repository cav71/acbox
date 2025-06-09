#!/usr/bin/env python
# ./support/builder.py src/acbox/version.py --data support/data/beta.full.json -n
from __future__ import annotations

import argparse
import contextlib
import dataclasses as dc
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Generator

logger = logging.getLogger(__name__)


@dc.dataclass
class GData:
    name: str = ""
    ref: str = ""
    sha: str = ""
    run_number: int | None = None
    build: int | None = None
    mode: str = ""
    branch_version: tuple[int] | None = None

    @staticmethod
    def extract_version(gdata: GData) -> tuple[str | None, tuple[int] | None]:
        expr = re.compile(r"^refs/heads/(?P<mode>(master|main))$")
        if match := expr.search(gdata.ref):
            return (match.group("mode"), None)

        expr = re.compile(r"^refs/tags/v(?P<v>\d+([.]\d+)*)")
        if match := expr.search(gdata.ref):
            return (
                "release",
                tuple(int(v) for v in match.group("v").split(".")),
            )

        expr = re.compile(r"^refs/heads/(?P<mode>(beta|release))/(?P<v>\d+([.]\d+)*)")
        if match := expr.search(gdata.ref):
            return (
                match.group("mode"),
                tuple(int(v) for v in match.group("v").split(".")),
            )
        return None, None


@dc.dataclass
class Git:
    exe: str = "git"

    def __post_init__(self):
        logger.debug("using git exe from: %s:", self.exe)

    def branch(self, name: str = "HEAD"):
        try:
            return runc([self.exe, "rev-parse", "--abbrev-ref", name], quiet=True).strip()
        except subprocess.CalledProcessError:
            logger.debug("failed command: %s", [self.exe, "rev-parse", "--abbrev-ref", name], exc_info=True)
            return None

    def commits_on_branch(self, main: str = "origin/main"):
        parent = runc([self.exe, "merge-base", self.branch(), main]).strip()
        return int(runc([self.exe, "rev-list", "--count", f"{parent}..{self.branch()}"]))


def runc(args: list[str | Path], quiet: bool = False) -> str:
    arguments = [str(a) for a in args]
    logger.debug("runc: %s", arguments)
    stderr = subprocess.DEVNULL if quiet else None
    return subprocess.check_output(arguments, encoding="utf-8", stderr=stderr)


def fetch_gitub_dump(github_dump: str) -> GData:
    gdata = GData()

    data = json.loads(Path(github_dump[1:]).read_text()) if github_dump.startswith("@") else json.loads(github_dump)
    if not data.get("version"):
        data["name"] = data["event"]["repository"]["name"]

    fields = [f.name for f in dc.fields(GData)]
    for key, value in data.items():
        if key.lower() in fields:
            setattr(gdata, key.lower(), value)
    if gdata.run_number is not None:
        gdata.run_number = int(gdata.run_number)

    # assign branch name and branch_version from github
    if gdata.mode or gdata.branch_version:
        raise RuntimeError("cannot set")
    gdata.mode, gdata.branch_version = GData.extract_version(gdata)
    return gdata


@contextlib.contextmanager
def backups() -> Generator[Callable[[str | Path], Path], None, None]:
    pathlist: list[Path] = []

    def save(path: Path | str) -> Path:
        nonlocal pathlist
        original = Path(path).expanduser().absolute()
        backup = original.parent / f"{original.name}.bak"
        if backup.exists():
            raise RuntimeError("backup file present", backup)
        shutil.copy(original, backup)
        pathlist.append(backup)
        return original

    try:
        yield save
    finally:
        for backup in pathlist:
            original = backup.with_suffix("")
            original.unlink()
            shutil.move(backup, original)


@dc.dataclass
class EditableFile:
    path: Path
    lines: list[str] = dc.field(default_factory=list)

    def __post_init__(self):
        self.lines = self.path.read_text().split("\n")

    def save(self):
        self.path.write_text("\n".join(self.lines))


@dc.dataclass
class ConfigFile(EditableFile):
    def find(self, call):
        result = []
        for lineno, line in enumerate(self.lines):
            if ret := call(line):
                result.append((lineno, line, ret))
        if len(result) > 1:
            raise RuntimeError(f"too many matches: {result}")
        return result[0] if result else (None, None, None)

    def find_var(self, key):
        expr = re.compile(r"\s*" + key + r"\s*[=]\s*(?P<quote>['\"])(?P<value>(\d+([.]\d)*)?)\1")
        return self.find(lambda line: expr.search(line))

    def replace_or_append(self, txt, lineno):
        if lineno is None:
            self.lines.append(txt)
        else:
            self.lines[lineno] = txt


def setup_logging(loglevel: list[int]) -> None:
    value = min(max(sum(loglevel or [0]), -1), 1)
    level = {
        -1: logging.WARNING,
        0: logging.INFO,
        1: logging.DEBUG,
    }[value]
    logging.basicConfig(level=level)


def parse_args(args=None):
    parser = argparse.ArgumentParser()

    group = parser.add_argument_group("logging", "logging related options")
    group.add_argument("-v", "--verbose", action="append_const", const=1, dest="loglevel", help="report verbose logging")
    group.add_argument("-q", "--quiet", action="append_const", const=-1, dest="loglevel", help="report quiet logging")

    parser.add_argument("--build", action="store_true", help="build the wheel")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--release", action="store_const", dest="mode", const="release")
    group.add_argument("--beta", action="store_const", dest="mode", const="beta")

    parser.add_argument("--main", default="origin/main", help="main branch")
    parser.add_argument("-n", "--dry-run", dest="dryrun", action="store_true", help="dry run")
    parser.add_argument("-c", "--config", dest="pyproject", default=Path("pyproject.toml"), type=Path, help="pyproject.toml file")
    parser.add_argument("--data", type=Path, help="source data from json file (debug only)")

    parser.add_argument("paths", type=Path, nargs="*", help="files to override")

    options = parser.parse_args(args)
    options.error = parser.error

    if not (os.getenv("GITHUB_DUMP") or options.data):
        parser.error("missing GITHUB_DUMP enviroment variable (or use --data)")
    options.data = f"@{options.data}" if options.data else os.getenv("GITHUB_DUMP")

    setup_logging(options.loglevel)

    return options


def main(args):
    git = Git()

    if git.branch(args.main) is None:
        args.error(f"cannot find branch data '{args.main}' (did you fetch all history?)")

    gdata = fetch_gitub_dump(args.data)
    gdata.build = git.commits_on_branch(args.main)

    with contextlib.ExitStack() as stack:
        store = stack.enter_context(backups())

        # pyproject.toml
        pyproject = ConfigFile(store(args.pyproject))
        lineno, line, ret = pyproject.find_var("version")
        current = ret.group("value")
        logger.info("current version %s from %s", current, args.pyproject)

        mode = args.mode or gdata.mode
        version = {
            "beta": f"{current}b{gdata.build}",
            "main": current,
            "release": current,
        }[mode]
        logger.info("using version %s [%s]", version, mode)

        if gdata.branch_version and (actual := tuple(int(c) for c in current.split("."))) != gdata.branch_version:
            args.error(f"working on branch version {gdata.branch_version} but current version {actual}")

        if current != version:
            logger.info("updating version in pyproject.toml: %s -> %s", current, version)
            pyproject.lines[lineno] = f'version = "{version}"'
            if not args.dryrun:
                pyproject.save()

        if args.build:
            from build import __main__

            logger.info("running: python -m build .")
            if not args.dryrun:
                __main__.main(["."])

        # TODO add processing more files
        sys.exit()

        # inifile
        for path in args.paths:
            initfile = ConfigFile(store(args.initfile))

        lineno, line, ret = initfile.find_var("__version__")
        initfile.replace_or_append(f'__version__ = "{version}"', lineno)

        lineno, line, ret = initfile.find_var("__hash__")
        initfile.replace_or_append(f'__hash__ = "{gdata["sha"]}"', lineno)

        initfile.save()

        if not args.dryrun:
            subprocess.check_call([sys.executable, "-m", "build"])  # noqa: S603


if __name__ == "__main__":
    main(parse_args())
