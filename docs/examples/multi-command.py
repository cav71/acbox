#!/usr/bin/env python3
"""simple test script"""
# /// script
# dependencies = [
# "acbox",
# ]
# ///

import logging

import click

from acbox.click import DEFAULT_OPTIONS, ArgsType, MainFn, group, options

log = logging.getLogger(__name__)


@group()
def main() -> None:
    "main doc text"
    pass


PARAMS0 = [2, 3, 4]
PARAMS1 = [5, 6, 7]


@options()
def func0_options(fn: MainFn) -> MainFn:
    return click.option("-x", type=int, default=0)(fn)


@func0_options.process
def func0_process(args: ArgsType) -> None:
    print(f"setting args.x to {args.x * PARAMS0[0]} = {args.x} * {PARAMS0[0]}")
    args.x = args.x * PARAMS0[0]


@func0_options.contextmanager
def func0_context(args: ArgsType):
    print(f"entering func0 with args.x {args.x}")

    def callback(value: int) -> int:
        print(f"post-processing result from func0 {value} * {PARAMS0[2]}")
        return value * PARAMS0[2]

    yield callback


@main.command(name="func0", aliases=["f", "f0"], options=[*DEFAULT_OPTIONS, func0_options])
def func0(args: ArgsType) -> int:
    "first simple function"
    return args.x * PARAMS0[1]


@options()
def func1_options(fn: MainFn) -> MainFn:
    return click.option("-y", type=int, default=0)(fn)


@func1_options.process
def func1_process(args: ArgsType) -> None:
    print(f"setting args.y to {args.y * PARAMS1[0]} = {args.y} * {PARAMS1[0]}")
    args.y = args.y * PARAMS1[0]


@func1_options.contextmanager
def func1_context(args: ArgsType):
    print(f"entering func1 with args.y {args.y}")

    def callback(value: int) -> int:
        print(f"post-processing result from func1 {value} * {PARAMS1[2]}")
        return value * PARAMS1[2]

    yield callback


@main.command(name="func1", aliases=["f1"], options=[*DEFAULT_OPTIONS, func1_options])
def func1(args: ArgsType) -> int:
    "second simple function"
    print(f"returning from func1 {args.y} * {PARAMS1[1]}")
    return args.y * PARAMS1[1]


if __name__ == "__main__":
    # set standalone_mode=True to handle internal errors
    ret = main(standalone_mode=False)
    print(f"final result -> {ret}")
