import functools
import logging
from argparse import Namespace
from typing import Callable

import click

TypeFn = Callable[[Namespace], None]


def add_loglevel(fn: TypeFn) -> TypeFn:
    fn = click.option("-v", "--verbose", count=True)(fn)
    fn = click.option("-q", "--quiet", count=True)(fn)
    return fn


def process_loglevel(options: Namespace, verbose_flag: bool = False) -> Namespace:
    level = max(min(options.__dict__.pop("verbose") - options.__dict__.pop("quiet"), 1), -1)

    # console = Console(theme=Theme({"log.time": "cyan"}))
    logging.basicConfig(
        level={-1: logging.WARNING, 0: logging.INFO, 1: logging.DEBUG}[level],
        # datefmt="[%X]",
        # handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
    if verbose_flag:
        options.verbose = level > 0
    return options


def clickwrapper(
    add_arguments: Callable[[TypeFn], TypeFn] | None = None,
    process_options: Callable[[Namespace], None | Namespace] | None = None,
    verbose_flag: bool = False,
) -> Callable[[TypeFn], None]:
    def _clickwrapper(fn: TypeFn):
        fn = add_loglevel(fn)
        if add_arguments:
            fn = add_arguments(fn)

        @functools.wraps(fn)
        def __clickwrapper(*args, **kwargs):
            options = Namespace(**kwargs)
            options = process_loglevel(options, verbose_flag=verbose_flag) or options
            if hasattr(options, "error"):
                raise RuntimeError("you have an error option")

            def error(msg):
                raise click.UsageError(msg)

            options.error = error
            if process_options:
                options = process_options(options) or options

            return fn(options)

        return __clickwrapper

    return _clickwrapper
