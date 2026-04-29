import logging

import click

import acbox.clickwrapper as cw
import acbox.config.servers
from acbox import clickextra
from acbox.clickwrapper import MainFn, Namespace

log = logging.getLogger(__name__)


def add_arguments(fn: MainFn) -> MainFn:
    fn = click.option("-x", type=int)(fn)
    return fn


def process_options(options: Namespace) -> Namespace:
    options.x = (options.x or 1) * 99
    options.config = acbox.config.servers.load(options.config)
    return options


@cw.group()
def main() -> None:
    pass


@main.command()
@cw.clickwrap("fancy", [clickextra.add_config("acbox/imap.yml"), add_arguments], process_options)
def hello(args: Namespace) -> None:
    """a test script"""
    log.debug("a debug level message")
    log.info("an info level message")
    log.warning("a warning level message")
    print(args.config.servers["cavallinux"])


if __name__ == "__main__":
    main()
