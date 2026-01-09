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
    fn = cw.click.option("-x", type=int)(fn)
    return fn


def process_options(options: Namespace) -> None:
    options.x = (options.x or 1) * 99


@cw.command("fancy", add_arguments, process_options)
def main(args: Namespace) -> None:
    log.debug("a debug level message")
    log.info("an info level message")
    log.warning("a warning level message")
    print(f"OUTPUT: {args.x}")


if __name__ == "__main__":
    main()
