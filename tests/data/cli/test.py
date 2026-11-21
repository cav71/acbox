from collections.abc import Callable, Generator

import click

from acbox.click import ArgsType, MainFn, command, options


@options()
def option0(fn: MainFn) -> MainFn:
    "the doubler"
    return click.option("--doubler", is_flag=True)(fn)


@option0.contextmanager
def option0_context(options: ArgsType) -> Generator[Callable, None, None]:
    "doubling action"

    def doubler(ret: int) -> int:
        if options.doubler or options.x == 8:
            print(f"AFTER DOUBLING -> {ret * 2}")
            return ret * 2
        return ret

    yield doubler


@options()
def option1(fn: MainFn) -> MainFn:
    "option1 doctext"
    return click.option("-x", type=int)(fn)


@option1.process
def process(args: ArgsType) -> None:
    "option1 process doctext"
    args.x = args.x or 0


@options()
def option2(fn: MainFn) -> MainFn:
    "option2 doctext"
    return click.option("-y", type=int)(fn)


@option2.process  # type: ignore[no-redef]
def process(args: ArgsType) -> ArgsType:  # noqa: F811
    "option2 process doctext"
    args.y = args.y or 0
    return args


@command(options=[option0, option1, option2])
def main(args: ArgsType) -> int:
    "hi there"
    print(f"Got for x {args.x}")
    print(f"Got for y {args.y}")
    return args.x + args.y
