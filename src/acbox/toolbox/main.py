# 1. info tool
# 2. replacer
import logging
import sys
from pathlib import Path

import click

from acbox.clickwrapper import Namespace, clickwrap, group

log = logging.getLogger(__name__)


@group()
def main():
    print("HELLO")


@main.command(aliases=["i", "info"])
@clickwrap("default")
def info(args: Namespace) -> None:
    "prints info data"
    from acbox.toolbox.info import main

    sys.exit(main())


def validate_define(ctx, param, values):
    if not values:
        return values
    for value in values:
        if value.count("=") != 1:
            raise click.BadParameter(f"{param.opts} must be in KEY=VALUE format: {value}")
    return dict(tuple(value.split("=")) for value in values)


@main.command(aliases=["r"])
@clickwrap("default")
@click.option("-D", "--define", callback=validate_define, multiple=True)
@click.option("-i", "--inplace", is_flag=True)
@click.option("-n", "--dry-run", is_flag=True)
@click.argument("files", nargs=-1)
def replace(args: Namespace) -> None:
    from acbox.toolbox.replacer import fix, process

    if not args.files:
        return
    if len(args.files) == 1 and not args.inplace:
        print(process(Path(args.files[0]).read_text(), defines=args.define))
        return

    if not args.inplace:
        args.error("with multiple sources, you need the -i|--inplace flag")

    for path in args.files:
        log.info("processing %s", path)
        fix(Path(path), defines=args.define, inplace=args.inplace)
