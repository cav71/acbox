from __future__ import annotations

import argparse
import inspect
import sys
from typing import Callable

# The return type of add_arguments

if sys.version_info >= (3, 10):
    ArgsCallback = Callable[[argparse.Namespace], None | argparse.Namespace]
else:
    ArgsCallback = Callable


class CliBaseError(Exception):
    pass


class AbortCliError(CliBaseError):
    pass


class AbortWrongArgumentError(CliBaseError):
    pass


def check_default_constructor(klass: type):
    signature = inspect.signature(klass.__init__)  # type: ignore[misc]
    for name, value in signature.parameters.items():
        if name in {"self", "args", "kwargs"}:
            continue
        if value.default is inspect.Signature.empty:
            raise RuntimeError(f"the {klass}() cannot be called without arguments")
