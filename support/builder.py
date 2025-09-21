#!/usr/bin/env python
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "click",
#   "jinja2",
# ]
# ///
from __future__ import annotations

import dataclasses as dc
import json
import logging
import os
import re
import sys
from argparse import Namespace
from pathlib import Path

import click
import jinja2

import acbox
from acbox.cli2 import TypeFn, clickwrapper
from acbox.fileops import backups
from acbox.git import Git
from acbox.runner import Runner

log = logging.getLogger(__name__)


@dc.dataclass
class GData:
    branch: str
    rev: str
    sha: str
    ref: str
    url: str
    main: str
    version: str


def add_arguments(fn: TypeFn) -> TypeFn:
    fn = click.option("-p", "--python", type=click.Path(exists=True, path_type=Path))(fn)
    fn = click.option("-n", "--dry-run", is_flag=True)(fn)
    fn = click.option("--release", is_flag=True)(fn)
    fn = click.option("--beta", is_flag=True)(fn)
    fn = click.option("--github")(fn)
    fn = click.argument("paths", nargs=-1, type=click.Path(exists=True, path_type=Path))(fn)
    return fn


def process_options(options: Namespace) -> None:
    if options.release and options.beta:
        raise click.BadParameter("--release and --beta are mutually exclusive")
    elif not (options.release or options.beta):
        raise click.BadParameter("need a --release or --beta flag")

    if not (options.github or os.getenv("GITHUB_DUMP")):
        raise click.BadParameter("need GITHUB_DUMP env variable or a --github option")

    options.github = json.loads(Path(options.github).read_text() if options.github else (os.getenv("GITHUB_DUMP") or ""))

    options.__dict__["dryrun"] = options.__dict__.pop("dry_run")


def find_version(pyproject: Path) -> tuple[int, str]:
    expr = re.compile(r"^\s*version\s*=\s*([\"'])(?P<version>[^\"']+)[\"']")
    result = []
    for lineno, line in enumerate(pyproject.read_text().split("\n")):
        if match := expr.search(line):
            result.append((lineno, match.group("version").strip()))

    if len(result) != 1:
        raise RuntimeError(f"found {len(result)} version lines, expected 1")
    return result[0]


def process_inplace(path: Path, gdata: GData):
    env = jinja2.Environment()
    env.globals = dict(gdata=gdata)
    tmpl = env.from_string(path.read_text())
    path.write_text(tmpl.render())


@click.command()
@clickwrapper(add_arguments, process_options, verbose_flag=True)
def main(args: Namespace) -> None:
    runc = Runner(verbose=args.verbose)
    gitx = Git.new(verbose=args.verbose, workdir=Path.cwd())

    log.info("python executable (%s) %s", (runc([sys.executable, "-V"], capture=True) or "").strip(), sys.executable)
    log.info("acbox from %s", acbox.__file__)
    log.info("git client using workdir %s", gitx.workdir)
    log.info("current branch is '%s'", gitx.branch())

    default_branch = args.github["event"]["repository"]["default_branch"]
    log.info("default branch '%s'", default_branch)

    pyproject = Path("pyproject.toml")
    lineno, version = find_version(pyproject)
    log.info("found version '%s'", version)

    # release only from a tag
    if args.release:
        if f"refs/tags/v{version}" != args.github["ref"]:
            raise click.UsageError(f"cannot release {version=}, current ref in github is {args.github['ref']}")
        newversion = version
    elif args.beta:
        count = gitx.commits_on_branch(f"origin/{default_branch}")
        newversion = f"{version}b{count}"
    log.info("releasing for '%s': %s -> %s", "release" if args.release else "beta", version, newversion)

    gdata = GData(
        branch=args.github["ref_name"],
        rev=args.github["sha"][:7],
        sha=args.github["sha"],
        ref=args.github["ref"],
        url=args.github["event"]["repository"]["html_url"],
        main=default_branch,
        version=newversion,
    )

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
