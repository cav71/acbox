#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click",
# ]
# ///
import collections
import copy
import json
import logging
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found, unused-ignore]

import acbox.clickwrapper as cw

from .. import secrets

log = logging.getLogger(__name__)


class Processor:
    @classmethod
    def collect(cls):
        result = []
        queue = collections.deque(cls.__subclasses__())
        while queue:
            item = queue.pop()
            result.append((item.name, item))
            for item in item.__subclasses__():
                queue.appendleft(item)
        return dict(result)

    @staticmethod
    def run(data: Mapping) -> None:
        pass


class KeepCaseBashProcessor(Processor):
    name = "bash"

    @staticmethod
    def _run(data: Mapping, upper: bool | None = None) -> None:
        if isinstance(data, Mapping):
            keys = []
            for key, value in data.items():
                keys.append(key.upper() if upper is True else key.lower() if upper is False else key)
                print(f'{keys[-1]}="{value}"')
            if data:
                print()
                print(f"export {' '.join(keys)}")
        else:
            print(data)

    @staticmethod
    def run(data: Mapping) -> None:
        KeepCaseBashProcessor._run(data)


class UpperCaseBashProcessor(KeepCaseBashProcessor):
    name = "bash+uppercase"

    @staticmethod
    def run(data: Any):
        KeepCaseBashProcessor._run(data, upper=True)


class LowerCaseBashProcessor(KeepCaseBashProcessor):
    name = "bash+lowercase"

    @staticmethod
    def run(data: Any):
        KeepCaseBashProcessor._run(data, upper=False)


def add_arguments(fn: cw.MainFn) -> cw.MainFn:

    fn = cw.cloup.option_group(
        "action",
        cw.click.option("-d", "--dump", is_flag=True),
        cw.click.option("--encrypt", is_flag=True),
        cw.click.option("--decrypt", is_flag=True),
        cw.cloup.constraints.AcceptAtMost(1),
    )(fn)

    fn = cw.cloup.option_group(
        "encryption",
        cw.click.option("-e", "--encrypted", is_flag=True, help="uses a private ssh key to descript the config file"),
        cw.click.option(
            "--encrypted-path", type=cw.click.Path(exists=False, dir_okay=False, resolve_path=True, path_type=Path)
        ),
    )(fn)

    fn = cw.click.option("-k", "--key", multiple=True)(fn)
    fn = cw.click.option("-m", "--mode", type=cw.click.Choice(Processor.collect()), default="bash+uppercase")(fn)
    fn = cw.click.argument(
        "config", type=cw.click.Path(exists=False, dir_okay=False, resolve_path=True, path_type=Path)
    )(fn)
    return fn


def process_options(options: cw.Namespace) -> None:
    options.config = secrets.SecretPath(
        options.config, key=secrets.lookup(options.encrypted_path) if options.encrypted else None
    )


def tget(data: Mapping, key: str = "", pointer: bool = False) -> Any:
    pos = []
    config = data
    if key:
        for k in key.split("."):
            pos.append(k)
            indexes = {c.upper(): c for c in config}
            if k.upper() not in indexes:
                raise ValueError(f"key '{'.'.join(pos)}' not found (full path '{key}')")
            config = config[indexes[k.upper()]]
    return config if pointer else copy.deepcopy(config)


def tgets(data: Mapping, keys: str | list[str] = "", pointer: bool = False) -> Any:
    dataset = []
    for key in [keys] if isinstance(keys, str) else keys:
        dataset.append((key, tget(data, key)))
    if len(dataset) == 1:
        return dataset[0][1]

    result: dict = {}
    for key, item in dataset:
        if not isinstance(item, Mapping):
            raise RuntimeError(f"cannot process non dict at '{key}': {item}")
        result.update(item)
    return result if pointer else copy.deepcopy(result)


def load_data(path: Path, keys: str | list[str] = "") -> Any:
    path = path.expanduser().resolve()
    data = tomllib.loads(path.read_text())
    return tgets(data, keys)


def process(data: Any, upper: bool = False) -> Any:
    if not hasattr(data, "items"):
        return data

    result = {}
    for key, value in data.items():
        key = key.upper() if upper else key
        value = str(value).strip('"').replace('"', '\\"')
        result[key] = value
    return result


def load(path: Path | str, keys: str | list[str] = "") -> Any:
    data = load_data(Path(path) if isinstance(path, str) else path, keys)
    if isinstance(data, Mapping):
        return {k.lower(): v for k, v in data.items()}
    return data


@cw.command("fancy", add_arguments, process_options)
def main(args: cw.Namespace) -> None:
    """reads data stored in a .toml file and dump values in a different format

    Eg.
        acbox-tomlcat -k some-key secrets.toml
    """
    data = load_data(args.config, args.key)
    if args.dump:
        print(json.dumps(data, indent=2) if isinstance(data, Mapping) else data)
        return
    elif args.encrypt:
        if key := secrets.lookup(args.encrypted_path):
            out = secrets.encrypt(args.config.read_text(), key=key)
            print(out.decode("utf-8"))
        else:
            print(args.config.read_text())
        return
    elif args.decrypt:
        print(args.config.read_text())
        return

    processor = Processor.collect()[args.mode]
    processor.run(data)


if __name__ == "__main__":
    main()
