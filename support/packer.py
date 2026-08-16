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
import tomllib

import acbox.packer
from acbox.clickwrapper import MainFn, command

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
    fn = click.argument("dependencies", nargs=-1)(fn)
    fn = click.argument("script", type=click.Path(exists=True, path_type=Path))(fn)
    fn = click.option("--versioned", is_flag=True)(fn)
    fn = click.option("-x", "--executable", is_flag=True)(fn)
    fn = click.option("-o", "--output", default="dist/")(fn)
    return fn


def process_options(args: Namespace) -> None:
    if (args.output[-1:] in {"/", "\\"}) or Path(args.output).is_dir():
        args.output = Path(args.output) / args.script.with_suffix(".pyz").name
    else:
        args.output = Path(args.output)

    if args.versioned:
        pyproject = tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text())
        version = pyproject["project"]["version"]
        name = args.output.with_suffix("")
        args.output = name.parent / f"{name.name}-{version}.pyz"


@command("default", add_arguments, process_options)
def main(args: Namespace) -> None:
    log.info("creating package out of '%s'", args.script)
    log.info("output %s", args.output)

    dependencies = [Path(d) if Path(d).exists() else d for d in args.dependencies]

    if subdirs := list((args.script.parent / "src").glob("*")):
        if len(subdirs) != 1:
            raise RuntimeError(f"cannot process src dirs in {args.script.parent}")
        dependencies.append(subdirs[0])
        log.debug("added sibling search subdir %s", dependencies[-1])

    # dependencies from script PEP 723
    embedded_dependencies = (acbox.packer.read_header(args.script) or {}).get("dependencies", [])
    for dependency in embedded_dependencies:
        if dependency in DEPS:
            log.debug("adding subdependencies for '%s': %s", dependency, ", ".join(DEPS[dependency]))
            dependencies.extend(DEPS[dependency])
        dependencies.append(dependency)

    dependencies = [MAPPER.get(dep, dep) for dep in dict.fromkeys(dependencies)]  # type: ignore

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with openpyz(args.output) as zfp:
        zfp.write(args.script, "__main__.py")

        for dependency in dependencies:
            if isinstance(dependency, Path):
                path = dependency
            else:
                path = Path(__import__(dependency).__file__)  # type: ignore
                log.info("adding dep %s from %s", dependency, relpath(path))
                if path.name != "__init__.py":
                    raise RuntimeError("unsupported")
                path = path.parent
            add_dir(zfp, path)

    if args.executable:
        with inplace(args.output) as (fp, data):
            fp.write(b"#!/usr/bin/env python3\n")
            fp.write(data)


if __name__ == "__main__":
    main()
