import argparse
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("paths", nargs="+", type=Path)
    return parser.parse_args()


def main(options: argparse.Namespace) -> None:
    allpaths = []
    for path in options.paths:
        allpaths.extend(list(path.rglob("__pycache__")))

    for path in sorted(allpaths):
        if not path.is_dir():
            continue
        print(f"{'(dry-run) ' if options.dry_run else ''}removing {path}")
        if options.dry_run:
            continue
        shutil.rmtree(path)


if __name__ == "__main__":
    main(parse_args())
