#!/usr/bin/env python3
"""simple test script"""
# /// script
# dependencies = [
# "acbox",
# ]
# ///

import logging
from argparse import Namespace

import acbox.clickwrapper as cw

log = logging.getLogger(__name__)


def add_arguments(fn: cw.MainFn) -> cw.MainFn:
    fn = cw.click.option("-a", type=int)(fn)
    fn = cw.cloup.option_group(
        "action",
        cw.click.option("-b", is_flag=True),
        cw.click.option("-c", is_flag=True),
        cw.click.option("-d", is_flag=True),
        cw.click.option("-e", is_flag=True),
        cw.cloup.constraints.AcceptAtMost(1),
    )(fn)
    return fn


def process_options(options: Namespace) -> None:
    options.a = (options.a or 1) * 99


@cw.command("fancy", add_arguments, process_options)
def main(args: Namespace) -> None:
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
        raise cw.click.ClickException("Something went wrong with your command!")
    elif args.d:
        raise cw.click.UsageError("An error in usage")
    elif args.e:
        raise cw.click.BadParameter("this parameter is bad", param_hint="-e|--e")


if __name__ == "__main__":
    main()
