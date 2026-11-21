#!/usr/bin/env python3
"""simple test script"""
# /// script
# dependencies = [
# "acbox",
# ]
# ///

import logging
import time
from collections.abc import Callable, Generator

import click
import cloup
import humanize

from acbox.click import DEFAULT_OPTIONS, ArgsType, MainFn, command, options

log = logging.getLogger(__name__)


@options()
def add_arguments(fn: MainFn) -> MainFn:
    fn = click.option("-a", type=int)(fn)
    fn = cloup.option_group(
        "action",
        click.option("-b", is_flag=True),
        click.option("-c", is_flag=True),
        click.option("-d", is_flag=True),
        click.option("-e", is_flag=True),
        cloup.constraints.AcceptAtMost(1),
    )(fn)
    return fn


@add_arguments.process
def process_options(options: ArgsType) -> None:
    options.a = (options.a or 1) * 99


@add_arguments.contextmanager
def app_wrapping(args: ArgsType) -> Generator[Callable, None, None]:
    t0 = time.monotonic()
    print("STARTING APP")

    def callback(*args, **kwargs):
        delta = time.monotonic() - t0
        fmt = humanize.naturaldelta(delta, minimum_unit="microseconds")
        print(f"ENDING APP AFTER {fmt}")

    yield callback


@command(options=[*DEFAULT_OPTIONS, add_arguments])
def main(args: ArgsType) -> None:
    log.debug("a debug level message")
    log.info("an info level message")
    log.warning("a warning level message")

    for key, value in sorted(args.__dict__.items()):
        if key in {"error", "exit", "verbose"}:
            continue
        print(f"{key=}: {value} ({type(value)})")

    # raise an error
    if args.b:
        raise RuntimeError("an error message", 99)
    elif args.c:
        raise click.ClickException("Something went wrong with your command!")
    elif args.d:
        raise click.UsageError("An error in usage")
    elif args.e:
        raise click.BadParameter("this parameter is bad", param_hint="-e|--e")


if __name__ == "__main__":
    main()
