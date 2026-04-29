from pathlib import Path
from typing import Callable

import click

from acbox.clickwrapper import MainFn


def add_config(path: Path | str) -> Callable[[MainFn], MainFn]:
    def _add_config(fn: MainFn) -> MainFn:
        return click.option("-c", "--config", type=Path, default=Path("~/.config").expanduser() / path)(fn)

    return _add_config
