#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click",
# ]
# ///
import json
import logging
from pathlib import Path
from typing import Any

import tomllib

import acbox.clickwrapper as cw

log = logging.getLogger(__name__)


def add_arguments(fn: cw.MainFn) -> cw.MainFn:
    fn = cw.click.option("-d", "--dump", is_flag=True)(fn)
    fn = cw.click.option("-k", "--key")(fn)
    fn = cw.click.option("-m", "--mode", type=cw.click.Choice(["bash", "bash+uppercase"]), default="bash+uppercase")(fn)
    fn = cw.click.argument(
        "config", type=cw.click.Path(exists=False, dir_okay=False, resolve_path=True, path_type=Path)
    )(fn)
    return fn


def process_options(options: cw.Namespace) -> None:
    pass


def load_data(path: Path, key: str = "") -> Any:
    path = path.expanduser().resolve()
    config = tomllib.loads(path.read_text())

    pos = []
    if key:
        for k in key.split("."):
            pos.append(k)
            indexes = {c.upper(): c for c in config}
            if k.upper() not in indexes:
                raise ValueError(f"key '{'.'.join(pos)}' not found (full path '{key}')")
            config = config[indexes[k.upper()]]
    return config


def process(data: Any, upper: bool = False) -> Any:
    if not hasattr(data, "items"):
        return data

    result = {}
    for key, value in data.items():
        key = key.upper() if upper else key
        value = str(value).strip('"').replace('"', '\\"')
        result[key] = value
    return result


def load(path: Path, key: str = "", upper: bool = False) -> Any:
    data = load_data(path, key)
    return process(data, upper)


@cw.command("fancy", add_arguments, process_options)
def main(args: cw.Namespace) -> None:
    data = load_data(args.config, args.key)
    if args.dump:
        print(json.dumps(data, indent=2))
        return

    data = process(data, args.mode == "bash+uppercase")

    if args.mode in {"bash", "bash+uppercase"}:
        if hasattr(data, "items"):
            for key, value in data.items():
                print(f'{key}="{value}')
            print()
            print(f"export {' '.join(data)}")
        else:
            print(data)


if __name__ == "__main__":
    main()
