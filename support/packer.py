#!/usr/bin/env python
import os
from pathlib import Path
import contextlib
import argparse
import shutil
import logging
import tarfile
from zipfile import ZipFile, ZIP_DEFLATED 


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


def parse_args() -> None:
    parser = argparse.ArgumentParser()

    group = parser.add_argument_group("logging", "logging control")
    group.add_argument("-v", "--verbose", dest="level", action="append_const", const=1)
    group.add_argument("-q", "--quiet", dest="level", action="append_const", const=-1)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-o", "--output", type=Path)
    group.add_argument("-i", "--inplace", action="store_true")

    parser.add_argument("script", type=Path)
    parser.add_argument("dependencies", nargs="*")


    args = parser.parse_args()
    args.error = parser.error

    level = min(max(sum(args.level or [0]), -1), 1)
    logging.basicConfig(
        level={-1: logging.WARNING, 0: logging.INFO, 1: logging.DEBUG}[level]
    )
    return args


def add_dir(zfp, path: Path):
    for root, dirs, files in os.walk(path):
        todrop = set()
        for i, d in enumerate(dirs):
            if d in {"__pycache__"}:
                todrop.add(i)
        for i in reversed(sorted(todrop or [])):
            del dirs[i]
        base = Path(root).relative_to(path.parent)
        for file in files:
            zfp.write(Path(root) / file, str(base / file))


def find_wheel(path: Path) -> Path:
    if not path.is_dir():
        log.debug("looking at (possibly) a wheel file in %s", path)
        return path
    candidates = list(path.glob("*.whl"))
    log.debug("scanning for wheels in %s, found: %s", path, candidates)
    return candidates


@contextlib.contextmanager
def generate(out: Path):
    with ZipFile(out, "a", compression=ZIP_DEFLATED) as zfp:
        yield zfp


def get_dependencies(zfp: ZipFile) -> list[str]:
    name = [name for name in zfp.namelist() if name.endswith("/METADATA")][0]
    with zfp.open(name) as myfile:
        dependencies = [
            line.split(":")[1].strip()
            for line in myfile.read().decode("utf-8").split("\n")
            if line.startswith("Requires-Dist:")
        ]
    return dependencies


def main(args: argparse.Namespace) -> None:
    if len(wheels := find_wheel(args.script)) != 1:
        args.error(f"found {'too many' if len(weels) else 'no'} whl files in {args.script}")
    wheel = wheels[0]
    log.info("processing wheel file %s", wheel)

    if args.inplace:
        output = wheel
    else:
        output = (args.output / wheel.name) if args.output.is_dir() else args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(wheel, output)
    log.info("output file in %s%s", output, " (in-place)" if args.inplace else "")
        
    with generate(output) as zfp:
        dependencies = get_dependencies(zfp)
        log.info("using dependencies: %s", dependencies)

        all_deps = set()
        for dep in dependencies:
            all_deps.add(dep)
            if extra := DEPS.get(dep, []):
                all_deps.update(extra)
                log.debug("as subdependency of %s, added: %s", dep, extra)

        for dep in sorted(all_deps):
            mod = __import__(MAPPER.get(dep, dep))
            path = Path(mod.__file__)
            if path.name == "__init__.py":
                add_dir(zfp, path.parent)
            else:
                raise RuntimeError("unsupported")


if __name__ == "__main__":
    main(parse_args())
