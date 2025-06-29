#!/usr/bin/env python
import argparse
import logging

from acbox.cli.flags.logging import add_arguments_logging
from acbox.cli.script import cli

log = logging.getLogger(__name__)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    add_arguments_logging(parser)


@cli(add_arguments)
def main(args: argparse.Namespace):
    # show some logging info
    log.debug("a debug message, need to use -v|--verbose to display it")
    log.info("an info message, you can silence it with -q|--quiet")
    log.warning("a warning!")

    # args is a argparse.Namespace instance. Attributes always defined are:
    #   .config - points to a config file might be present or not
    #   .error - callable, to abort a script with a nice error message
    #   .modules - list of modules leading to this script

    print("args:")
    for name in dir(args):
        if name.startswith("_"):
            continue
        value = getattr(args, name)
        kind = type(value)
        if name == "error":
            kind, value = "callable", "abort a script with an error message"
        if kind is list:
            print(f"  .{name}: ({kind})")
            for item in value:
                print(f"     {item}")
        else:
            print(f"  .{name}: ({kind}) {value}")


if __name__ == "__main__":
    main()
