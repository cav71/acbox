#!/usr/bin/env python
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "acbox",
# ]
# ///


import contextlib
import logging
import os
from argparse import Namespace
from pathlib import Path
from typing import IO, Generator
from zipfile import ZIP_DEFLATED, ZipFile

import click

import acbox.packer
from acbox.clickwrapper import MainFn, clickwrap, command

DEPS = {
    # uv tree --package rich
    "rich": [
        "markdown-it-py",
        "mdurl",
        "pygments",
    ],
}
MAPPER = {
    "markdown-it-py": "markdown_it",
}


log = logging.getLogger(__name__)


def relpath(path: Path) -> Path:
    with contextlib.suppress(ValueError):
        return path.relative_to(Path.cwd())
    return path


@contextlib.contextmanager
def inplace(path: Path) -> Generator[tuple[IO, bytes], None, None]:
    data = path.read_bytes()
    try:
        yield open(path, "wb"), data
    except Exception:
        path.write_bytes(data)
        raise


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


def add_arguments(fn: MainFn) -> MainFn:
    click.argument("script", type=click.Path(exists=True, path_type=Path))(fn)
    click.option("-o", "--output", default="dist/")(fn)
    return fn


def process_options(args: Namespace) -> None:
    if (args.output[-1:] in {"/", "\\"}) or Path(args.output).is_dir():
        args.output = Path(args.output) / args.script.with_suffix(".pyz").name
    else:
        args.output = Path(args.output)


@command()
@clickwrap("default", add_arguments, process_options)
@click.option("-x", "--executable", is_flag=True)
def main(args: Namespace) -> None:
    breakpoint()
    log.info("creating package out of '%s'", args.script)
    log.info("output %s", args.output)

    subdir = None
    if subdirs := list((args.script.parent / "src").glob("*")):
        if len(subdirs) != 1:
            raise RuntimeError(f"cannot process src dirs in {args.script.parent}")
        subdir = subdirs[0]

    args.output.parent.mkdir(parents=True, exist_ok=True)

    dependencies = set()
    for dep in acbox.packer.read_header(args.script).get("dependencies", []):
        dependencies.add(dep)
        dependencies.update(DEPS.get(dep, set()))

    with openpyz(args.output) as zfp:
        zfp.write(args.script, "__main__.py")
        if subdir:
            add_dir(zfp, subdir)
        for dependency in sorted(dependencies):
            mod = __import__(MAPPER.get(dependency, dependency))
            path = Path(str(mod.__file__))
            log.info("adding dep %s from %s", dependency, relpath(path))
            if path.name == "__init__.py":
                add_dir(zfp, path.parent)
            else:
                raise RuntimeError("unsupported")

    if args.executable:
        with inplace(args.output) as (fp, data):
            fp.write(b"#!/usr/bin/env python3\n")
            fp.write(data)


if __name__ == "__main__":
    main()
