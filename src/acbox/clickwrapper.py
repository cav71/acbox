import functools
import inspect
import logging
from argparse import Namespace
from typing import Callable

import click
import cloup
from cloup import HelpFormatter, HelpTheme, Style, option_group

TypeFn = Callable[[Namespace], None]


formatter_settings = HelpFormatter.settings(
    theme=HelpTheme(
        invoked_command=Style(fg="bright_yellow"),
        heading=Style(fg="bright_white", bold=True),
        constraint=Style(fg="magenta"),
        col1=Style(fg="bright_yellow"),
    )
)


def command(*args, **kwargs):
    def _fn(func):
        func = cloup.command(formatter_settings=formatter_settings)(func)
        return func

    return _fn


def add_loglevel(fn: TypeFn) -> TypeFn:
    fn = option_group(
        "log level",
        click.option("-v", "--verbose", count=True, help="increase level"),
        click.option("-q", "--quiet", count=True, help="decrease level"),
    )(fn)
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
        if add_arguments and not callable(fn := add_arguments(fn)):
            raise RuntimeError(f"function {add_arguments} must return a callable TypeFn (source={inspect.getfile(add_arguments)})")

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
