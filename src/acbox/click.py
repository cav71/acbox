import argparse
import contextlib
import functools
import logging

import click
import cloup

from .clickextra import options, parse_options_argument

STANDARD_OPTIONS = ["logging", "dryrun"]


@options(register="logging")
def logging_options(fn):
    fn = cloup.option_group(
        "loglevel",
        click.option("-q", "--quiet", count=True),
        click.option("-v", "--verbose", count=True),
    )(fn)
    return fn


@logging_options.process
def process_logging(args):
    if hasattr(args, "loglevel"):
        raise RuntimeError("a loglevel option has been already set elsewhere")
    args.loglevel = args.__dict__.pop("verbose", 0) - args.__dict__.pop("quiet", 0)

    logging.basicConfig(
        level={
            -1: logging.WARNING,
            0: logging.INFO,
            1: logging.DEBUG,
        }[max(min(args.loglevel, 1), -1)]
    )
    return args


@options(register="dryrun")
def dryrun(fn):
    return click.option("-n", "--dry-run", is_flag=True)(fn)
    return fn


@dryrun.process
def process_dryrun(args):
    if hasattr(args, "dryrun"):
        raise RuntimeError("a dryrun option has been already set elsewhere")
    args.dryrun = args.__dict__.pop("dry_run")


def command(*args0, **kwargs0):
    optionfns = parse_options_argument(kwargs0.pop("options", STANDARD_OPTIONS))

    def _command0(fn):
        @functools.wraps(fn)
        def _command1(*args, **kwargs):
            options = argparse.Namespace(**kwargs)
            for optionfn in optionfns:
                if not optionfn.process_options:
                    continue
                options = optionfn.process_options(options) or options
            with contextlib.ExitStack() as stack:
                for optionfn in optionfns:
                    if not optionfn.with_context:
                        continue
                    stack.enter_context(optionfn.with_context(options))
                return fn(options)

        wrapped = _command1
        for optionfn in optionfns:
            wrapped = optionfn(wrapped)
        wrapped = cloup.command()(wrapped)
        return wrapped

    return _command0
