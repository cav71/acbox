#!/usr/bin/env python
"""Run quality check on code
Layout:
├── src
│   └── acbox
│       └─ cli
│          └─ shared.py
└── tests
 └── test_cli_shared.py
"""

import argparse
import dataclasses as dc
import json
import logging
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

logger = logging.getLogger("quality")


@dc.dataclass
class TestCase:
    classname: str
    name: str
    time: float
    failures: list[str] = dc.field(default_factory=list)


def find_package() -> tuple[str | None, Path | None]:
    if (src := Path("src")).exists():
        items = [path for path in src.glob("*") if not (path.name.startswith(".") or path.name.endswith(".egg-info"))]
        if len(items) == 1:
            return items[0].name, items[0].resolve()
    return None, None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-t", "--test-dirs", action="append", type=Path)

    package_default, package_source_default = find_package()
    parser.add_argument("-p", "--package", default=package_default)
    parser.add_argument("-s", "--package-source", type=Path, default=package_source_default)

    parser.add_argument("-c", "--coverage", action="store_true")

    parser.add_argument("sources", type=Path, nargs="+")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)

    if args.test_dirs is None:
        args.test_dirs = [Path("tests").resolve()]
    args.test_dirs = [d.resolve() for d in args.test_dirs]

    if not (args.package_source and args.package_source.exists()):
        parser.error("need to provide a package source dir")

    if missing := [source for source in args.sources if not source.exists()]:
        parser.error(f"cannot find {', '.join(str(s) for s in missing)}")
    args.sources = [s.resolve() for s in args.sources]

    return args


def candidates(path: Path, package: Path, dirs: list[Path]) -> list[Path] | None:
    try:
        relpath = path.relative_to(package)
    except ValueError:
        return None
    candidates = []
    for tdir in dirs:
        if (test := tdir / relpath.parent / f"test_{path.name}").exists():
            candidates.append(test)
    return candidates


def process_xml(txt: str) -> list[TestCase]:
    root = ET.fromstring(txt)
    result = []
    for testsuite in root:
        for testcase in testsuite:
            failures = []
            for item in testcase:
                if item.tag == "failure":
                    failures.append(item.attrib["message"])
            kwargs = {}
            for key, fn in [("classname", str), ("name", str), ("time", float)]:
                kwargs[key] = fn(testcase.attrib[key])
            result.append(TestCase(**kwargs))
    return result


def run(tests: dict[str, list[Path]], cov: str) -> tuple[str, str]:
    args: list[str | Path] = [
        "pytest",
        "-vvs",
    ]

    tmpdir = Path(tempfile.mkdtemp())
    try:
        args += [
            "--junit-xml",
            tmpdir / "junit.xml",
        ]
        if cov:
            args += [
                "--cov",
                "acbox",
                "--cov-report",
                f"json:{tmpdir / 'coverage.json'}",
            ]
        args += [str(t) for tt in tests.values() for t in tt]
        subprocess.call(args)
        return (tmpdir / "junit.xml").read_text(), (tmpdir / "coverage.json").read_text()
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main(args):
    logger.info("package '%s' location %s", args.package, args.package_source)
    logger.info("test directories %s", args.test_dirs)

    tests = {}
    for source in args.sources:
        logger.info("processing %s", source)
        if (paths := candidates(source, args.package_source, args.test_dirs)) is None:
            logger.warning("skipping source not inside package dir, %s", source)
            continue
        logger.info("test targets %s", paths)
        key = source.relative_to(args.package_source)
        tests[key] = paths

    if tests:
        junit, coverage = run(tests, args.coverage)
        for test in process_xml(junit):
            if test.failures:
                print(test)

        coverages = json.loads(coverage)
        for source in args.sources:
            path = source.relative_to(Path.cwd())
            module_source = source.relative_to(args.package_source)
            coverage = coverages["files"][str(path)]
            total_pct = coverage["summary"]["percent_covered"]
            print(f"{module_source} {total_pct}")


if __name__ == "__main__":
    args = parse_args()
    main(args)
