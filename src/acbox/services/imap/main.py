import logging

import click

import acbox.config.servers
from acbox.click import DEFAULT_OPTIONS, ArgsType, MainFn, group, options

log = logging.getLogger(__name__)


@options()
def add_arguments(fn: MainFn) -> MainFn:
    fn = click.option("-x", type=int)(fn)
    return fn


@add_arguments.process
def process_options(options: ArgsType) -> ArgsType:
    options.x = (options.x or 1) * 99
    options.config = acbox.config.servers.load(options.config)
    return options


@group(options=[*DEFAULT_OPTIONS, add_arguments])
def main() -> None:
    pass


@main.command()
# @cw.clickwrap("fancy", [clickextra.add_config("acbox/imap.yml"), add_arguments], process_options)
def hello(args: ArgsType) -> None:
    """a test script"""
    log.debug("a debug level message")
    log.info("an info level message")
    log.warning("a warning level message")
    print(args.config.servers["cavallinux"])


if __name__ == "__main__":
    main()
