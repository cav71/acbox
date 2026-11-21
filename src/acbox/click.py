import contextlib
import functools
import logging
from argparse import Namespace
from collections.abc import Callable
from typing import Any

import click
import cloup
import darkdetect

from .clickextra import ArgsType, MainFn, options, parse_options_argument

DEFAULT_OPTIONS = ["logging", "dryrun"]


@options(register="logging")
def logging_options(fn: MainFn) -> MainFn:
    fn = cloup.option_group(
        "loglevel",
        click.option("-q", "--quiet", count=True),
        click.option("-v", "--verbose", count=True),
    )(fn)
    return fn


@logging_options.process
def process_logging(args: ArgsType) -> ArgsType:
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
def dryrun(fn: MainFn) -> MainFn:
    return click.option("-n", "--dry-run", is_flag=True)(fn)
    return fn


@dryrun.process
def process_dryrun(args: ArgsType) -> None:
    if hasattr(args, "dryrun"):
        raise RuntimeError("a dryrun option has been already set elsewhere")
    args.dryrun = args.__dict__.pop("dry_run")


def command(*args0, **kwargs0) -> Callable[[MainFn], Any]:
    optionfns = parse_options_argument(kwargs0.pop("options", DEFAULT_OPTIONS))

    def _command0(fn: MainFn):
        @functools.wraps(fn)
        def _command1(*args, **kwargs):
            options = Namespace(**kwargs)
            for optionfn in optionfns:
                if not optionfn.process_options:
                    continue
                options = optionfn.process_options(options) or options
            callbacks = []
            with contextlib.ExitStack() as stack:
                for optionfn in optionfns:
                    if not optionfn.with_context:
                        continue
                    if callable(ctx := stack.enter_context(optionfn.with_context(options))):
                        callbacks.append(ctx)
                ret = fn(options)
            for callback in callbacks:
                ret = callback(ret)
            return ret

        wrapped = _command1
        for optionfn in optionfns:
            wrapped = optionfn(wrapped)

        kwargs0["formatter_settings"] = kwargs0.get("formatter_settings") or cloup.HelpFormatter.settings(
            theme=cloup.HelpTheme.dark() if darkdetect.isDark() else cloup.HelpTheme.light()
        )
        cmd = cloup.command(*args0, **kwargs0)(wrapped)
        assert not getattr(cmd, "fn", None)
        cmd.fn = fn
        return cmd

    return _command0
