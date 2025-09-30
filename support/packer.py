#!/usr/bin/env python
# 1. process the script header
# 2. use wheel.wheelfile to pack it

import contextlib
import logging
import os
from argparse import Namespace
from pathlib import Path
from typing import Generator
from zipfile import ZIP_DEFLATED, ZipFile

import click

import acbox.packer
from acbox.clickwrapper import TypeFn, clickwrapper

DEPS = {
    # subdependencies (eg. if you include rich, you need also these)
    # use `uv tree --package rich` to figure it out
    "rich": [
        "markdown-it-py",
        "mdurl",
        "linkify-it-py",
        "uc-micro-py",
        "mdit-py-plugins",
        "pygments",
    ],
}
# change spelling of dependencies
MAPPER = {
    "linkify-it-py": "linkify_it",
    "markdown-it-py": "markdown_it",
    "mdit-py-plugins": "mdit_py_plugins",
    "uc-micro-py": "uc_micro",
}


log = logging.getLogger(__name__)


def relpath(path: Path) -> Path:
    with contextlib.suppress(ValueError):
        return path.relative_to(Path.cwd())
    return path


@contextlib.contextmanager
def openpyz(out: Path) -> Generator[ZipFile, None, None]:
    with ZipFile(out, "w", compression=ZIP_DEFLATED, allowZip64=True) as zfp:
        yield zfp


def add_dir(zfp: ZipFile, path: Path) -> None:
    for root, dirs, files in os.walk(path):
        todrop = set()
        for i, d in enumerate(dirs):
            if d in {"__pycache__"}:
                todrop.add(i)
        for i in reversed(sorted(todrop or [])):
            del dirs[i]
        base = Path(root).relative_to(path.parent)
        for file in files:
            if ".so" in file:
                log.warning("skipping binary file %s", file)
                continue
            zfp.write(Path(root) / file, str(base / file))


def add_arguments(fn: TypeFn) -> TypeFn:
    click.option("-o", "--output", default="dist/")(fn)
    click.argument("dependencies", nargs=-1)(fn)
    click.argument("script", type=click.Path(exists=True, path_type=Path))(fn)
    return fn


def process_options(args: Namespace) -> None:
    if (args.output[-1:] in {"/", "\\"}) or Path(args.output).is_dir():
        args.output = Path(args.output) / args.script.with_suffix(".pyz").name
    else:
        args.output = Path(args.output)


@click.command()  # type: ignore
@clickwrapper(add_arguments, process_options, verbose_flag=True)
def main(args: Namespace) -> None:
    log.info("creating package out of '%s'", args.script)
    log.info("output %s", args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # dependencies come from command line
    dependencies = []
    for dep in args.dependencies:
        log.debug("added cli dependency %s", dep)
        dependencies.append(dep)
        dependencies.extend(DEPS.get(dep, []))

    # pull dependencies from the script itself (pep 723)
    for dep in (acbox.packer.read_header(args.script) or {}).get("dependencies", []):
        log.debug("added cli dependency from script %s", dep)
        dependencies.append(dep)
        dependencies.extend(DEPS.get(dep, []))

    for index, dep in enumerate(dependencies):
        if (path := Path(dep)).exists():
            dependencies[index] = path

    with openpyz(args.output) as zfp:
        zfp.write(args.script, "__main__.py")
        for dep in dependencies:
            if isinstance(dep, str):
                mod = __import__(MAPPER.get(dep, dep))
                path = Path(str(mod.__file__))
                if path.name == "__init__.py":
                    path = path.parent
            else:
                path = Path(dep)
            log.info("adding dep %s from %s", dep, relpath(path))
            add_dir(zfp, path)

    log.info(f"generated {args.output}")


if __name__ == "__main__":
    main()
