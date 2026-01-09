#!/usr/bin/env python
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "build",
#   "click",
#   "httpx",
#   "jinja2",
# ]
# ///
from __future__ import annotations

import contextlib
import dataclasses as dc
import functools
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from typing import Callable, Generator, Literal

import click
import httpx
import jinja2
import tomllib

MainFn = Callable[[Namespace], int | None]
AddArgFn = Callable[[MainFn], MainFn]
ProcessOptionsFn = Callable[[Namespace], None | Namespace]

log = logging.getLogger(__name__)


@contextlib.contextmanager
def backups() -> Generator[Callable[[Path | str], tuple[Path, Path]], None, None]:
    pathlist: list[Path] = []

    def save(path: Path | str) -> tuple[Path, Path]:
        nonlocal pathlist
        original = Path(path).expanduser().absolute()
        backup = original.parent / f"{original.name}.bak"
        if backup.exists():
            raise RuntimeError("backup file present", backup)
        shutil.copy(original, backup)
        pathlist.append(backup)
        return original, backup

    try:
        yield save
    finally:
        for backup in pathlist:
            original = backup.with_suffix("")
            original.unlink()
            shutil.move(backup, original)


@dc.dataclass
class GData:
    name: str  # acbox
    ref: str  # refs/heads/beta/0.0.2
    sha: str  # 33eebf59f98adc51ee62f4db4a9ced2cb84bdaa2
    rev: str  # 33eebf5
    url: str  # ?
    run_number: int  # 123
    default_branch: str  # <default-branch eg. main|master>
    branch: str

    # these are added here
    kind: Literal["beta", "release", "main"]
    version: str
    count: int | None


@dc.dataclass
class Runner:
    exe: list[str] | None = None
    verbose: bool = False

    def __call__(self, args, verbose: bool | None = None, capture=False):
        verbose = self.verbose if verbose is None else verbose
        cmd = [str(c) for c in [*(self.exe or []), *args]]
        if capture:
            return subprocess.check_output(cmd, encoding="utf-8", stderr=None if verbose else subprocess.DEVNULL)
        return subprocess.check_call(
            cmd, encoding="utf-8", stderr=None if verbose else subprocess.DEVNULL, stdout=None if verbose else subprocess.DEVNULL
        )


@dc.dataclass
class Git:
    worktree: Path
    runner: Runner

    @classmethod
    def new(cls, worktree: Path, verbose: bool = False):
        return cls(worktree, Runner(exe=["git", "--git-dir", f"{worktree}/.git"], verbose=verbose))

    def branch(self):
        return self.runner(["branch", "--show-current"], capture=True).strip()


def add_arguments(fn):
    fn = click.option("-q", "--quiet", count=True)(fn)
    fn = click.option("-v", "--verbose", count=True)(fn)
    fn = click.option("-p", "--python", type=click.Path(exists=True, path_type=Path))(fn)
    fn = click.option("-n", "--dry-run", is_flag=True)(fn)
    fn = click.option("--release", is_flag=True)(fn)
    fn = click.option("--beta", is_flag=True)(fn)
    fn = click.option("--github")(fn)
    fn = click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))(fn)
    return fn


def process_options(options: Namespace) -> None:
    verbose = (options.__dict__.pop("verbose") if "verbose" in options.__dict__ else 0) - (
        options.__dict__.pop("quiet") if "quiet" in options.__dict__ else 0
    )
    level = {-1: logging.WARNING, 0: logging.INFO, 1: logging.DEBUG}[min(max(verbose, -1), 1)]
    logging.basicConfig(level=level)
    options.verbose = level > logging.INFO

    def error(msg):
        raise click.UsageError(msg)

    options.error = error
    if options.release and options.beta:
        raise click.BadParameter("--release and --beta are mutually exclusive")
    elif not (options.release or options.beta):
        raise click.BadParameter("need a --release or --beta flag")

    if not (options.github or os.getenv("GITHUB_DUMP")):
        raise click.BadParameter("need GITHUB_DUMP env variable or a --github option")

    if options.github:
        log.debug("github definition from cli %s", options.github)
        options.github = json.loads(Path(options.github).read_text())
    else:
        log.debug("github definition from GITHUB_DUMP: %s", os.environ.get("GITHUB_DUMP", "N/A"))
        options.github = json.loads(os.environ["GITHUB_DUMP"])

    options.__dict__["dryrun"] = options.__dict__.pop("dry_run")


def command():
    def _clickwrapper(fn: MainFn):
        @functools.wraps(fn)
        def _fn(fn: MainFn):
            def __fn(*args, **kwargs):
                options = Namespace(**kwargs)
                process_options(options)
                return fn(options)

            return __fn

        fn = _fn(fn)
        fn = click.command()(fn)
        fn = add_arguments(fn)
        return fn

    return _clickwrapper


def find_version(pyproject: Path) -> tuple[int, str]:
    expr = re.compile(r"^\s*version\s*=\s*([\"'])(?P<version>[^\"']+)[\"']")
    result = []
    for lineno, line in enumerate(pyproject.read_text().split("\n")):
        if match := expr.search(line):
            result.append((lineno, match.group("version").strip()))

    if len(result) != 1:
        raise RuntimeError(f"found {len(result)} version lines, expected 1")
    return result[0]


def parse_ref(ref: str, default_branch: str) -> tuple[Literal["beta", "release", "main"], str | None]:
    # ref is:
    #   refs/heads/beta/0.0.0
    #   refs/heads/main
    #   refs/tags/v0.0.0
    # returns -> (kind, branch_version)

    if match := re.search(r"refs/tags/v(?P<version>\d+([.]\d+)*)", ref):
        return ("release", match.group("version"))
    elif match := re.search(r"refs/heads/beta/(?P<version>\d+([.]\d+)*)", ref):
        return ("beta", match.group("version"))
    elif ref == f"refs/heads/{default_branch}":
        return ("main", None)
    raise RuntimeError(f"cannot parse {ref=}")


def process_inplace(path: Path, gdata: GData) -> None:
    env = jinja2.Environment()
    env.globals = dict(gdata=gdata)
    tmpl = env.from_string(path.read_text())
    path.write_text(tmpl.render())


def get_new_beta_number(name: str, version: str) -> int:
    txt = httpx.get(f"https://pypi.org/pypi/{name}/json").json()
    values = [int(r.partition("b")[2]) for r in txt["releases"] if r.startswith(f"{version}b")]
    return (max(values) + 1) if values else 0


@command()
def main(args: Namespace) -> None:
    runc = Runner(verbose=args.verbose)

    gitx = Git.new(Path.cwd(), verbose=args.verbose)

    log.info("python executable (%s) %s", (runc([sys.executable, "-V"], capture=True) or "").strip(), sys.executable)
    log.info("git client using worktree %s", gitx.worktree)
    log.info("current branch is '%s'", gitx.branch())

    # X default branch
    default_branch = args.github["event"]["repository"]["default_branch"]
    log.info("default branch '%s'", default_branch)

    pyproject = Path("pyproject.toml")
    # X version
    lineno, version = find_version(pyproject)
    name = tomllib.loads(pyproject.read_text())["project"]["name"]
    log.info("processing project '%s' @ %s", name, version)

    # X branch, count, newversion
    kind, branch_version = parse_ref(args.github["ref"], default_branch)

    if args.release:
        if kind != "release":
            raise click.UsageError(f"cannot release {version=}, current ref in github is {args.github['ref']}")
        count = None
        newversion = version
    elif args.beta:
        if kind != "beta":
            raise click.UsageError(f"cannot release beta {version=}, current ref in github is {args.github['ref']}")
        count = get_new_beta_number(name, version)
        newversion = f"{version}b{count}"
    else:
        raise RuntimeError("un-handled branch!")

    log.info("releasing for '%s': %s -> %s", kind, version, newversion)
    log.debug("ref = %s, count = %s, newversion = %s", args.github["ref"], count, newversion)

    gdata = GData(
        name=args.github["event"]["repository"]["name"],
        ref=args.github["ref"],  # refs/heads/beta/0.0.2
        sha=args.github["sha"],  # 33eebf59f98adc51ee62f4db4a9ced2cb84bdaa2
        rev=args.github["sha"][:7],  # 33eebf5
        url=f"{args.github['event']['repository']['html_url']}/tree/{args.github['ref_name']}",
        run_number=int(args.github["run_number"] or 0),
        default_branch=args.github["event"]["repository"]["default_branch"],
        branch=args.github["ref_name"],
        kind=kind,  # beta | release
        version=newversion,
        count=count,
    )

    if args.beta and gdata.branch != (current := f"beta/{version}"):
        args.error(f"version is '{version}', but building in branch {gdata.branch} (expected {current})")

    with backups() as save:
        save(pyproject)
        lines = pyproject.read_text().split("\n")
        lines[lineno] = f'version = "{newversion}"'
        pyproject.write_text("\n".join(lines))

        for path in args.paths:
            log.info("processing '%s'", path)
            save(path)
            process_inplace(path, gdata)

        log.info("building wheel package")
        if not args.dryrun:
            runc([args.python or sys.executable, "-m", "build", "."], verbose=True)


if __name__ == "__main__":
    main()
