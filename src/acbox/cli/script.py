from __future__ import annotations

import argparse
import contextlib
import functools
import inspect
import logging
import sys
import time
from typing import Any, Callable

from .parsers.base import ArgumentParserBase
from .parsers.simple import ArgumentParser
from .shared import AbortCliError, AbortWrongArgumentError

log = logging.getLogger(__name__)


@contextlib.contextmanager
def setup(
    function: Callable,
    add_arguments: (Callable[[ArgumentParserBase], None] | Callable[[argparse.ArgumentParser], None] | None) = None,
    process_args: (Callable[[argparse.Namespace], argparse.Namespace | None] | None) = None,
):
    sig = inspect.signature(function)
    module = inspect.getmodule(function)

    # the cli decorated function might have two special parameters:
    #  - args this will receive non-parsed arguments (eg from nargs="*")
    #  - parser escape hatch to the parser object (probably never used)
    if "args" in sig.parameters and "parser" in sig.parameters:
        raise RuntimeError(f"function '{module}.{function.__name__}' cannot take args and parser at the same time")

    # doc is taken from the function itself or the containing module
    description, _, epilog = (function.__doc__ or module.__doc__ or "").strip().partition("\n")
    epilog = f"{description}\n{'-' * len(description)}\n{epilog}"
    description = ""

    # extract parser info/fallbacks from all these modules
    modules = [
        sys.modules[__name__],
    ]
    if module:
        modules.append(module)

    parser = ArgumentParser.get_parser(modules, description=description, epilog=epilog)
    if add_arguments and (callbacks := add_arguments(parser)):
        if isinstance(callbacks, list):
            parser.callbacks.extend(callbacks)
        else:
            parser.callbacks.append(callbacks)

    kwargs = {}
    if "parser" in sig.parameters:
        kwargs["parser"] = parser

    t0 = time.monotonic()
    success = "completed"
    errormsg = ""
    show_timing = True
    # breakpoint()
    try:
        if "parser" not in sig.parameters:
            args = parser.parse_args()
            if process_args:
                args = process_args(args) or args

            if "args" in sig.parameters:
                kwargs["args"] = args
        yield sig.bind(**kwargs)

    except argparse.ArgumentError:
        sys.exit(2)
        pass
    except AbortCliError as exc:
        show_timing = False
        if exc.args:
            print(str(exc), file=sys.stderr)
        sys.exit(2)
    except AbortWrongArgumentError as exc:
        show_timing = False
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: {exc.args[0]}", file=sys.stderr)
        sys.exit(2)
    except SystemExit as exc:
        show_timing = False
        sys.exit(exc.code)
    except Exception:
        log.exception("un-handled exception")
        success = "failed with an exception"
    finally:
        if show_timing:
            delta = round(time.monotonic() - t0, 2)
            log.debug("task %s in %.2fs", success, delta)
    if errormsg:
        parser.error(errormsg)


def cli(
    add_arguments: (Callable[[ArgumentParserBase], Any] | Callable[[argparse.ArgumentParser], Any] | None) = None,
    process_args: (Callable[[argparse.Namespace], argparse.Namespace | None] | None) = None,
):
    def _cli1(function):
        module = inspect.getmodule(function)

        if inspect.iscoroutinefunction(function):

            @functools.wraps(function)
            async def _cli2(*args, **kwargs):
                with setup(function, add_arguments, process_args) as ba:
                    return await function(*ba.args, **ba.kwargs)

        else:

            @functools.wraps(function)
            def _cli2(*args, **kwargs):
                with setup(function, add_arguments, process_args) as ba:
                    return function(*ba.args, **ba.kwargs)

        _cli2.attributes = {
            "doc": function.__doc__ or module.__doc__ or "",
        }
        return _cli2

    return _cli1
