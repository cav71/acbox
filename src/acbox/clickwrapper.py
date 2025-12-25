import functools
import logging
from argparse import Namespace
from typing import Any, Callable, Sequence

import click
import cloup

MainFn = Callable[[Namespace], int | None]
AddArgFn = Callable[[MainFn], MainFn]
ProcessOptionsFn = Callable[[Namespace], None | Namespace]


def add_loglevel(fn: MainFn) -> MainFn:
    fn = cloup.option_group("loglevel", click.option("-q", "--quiet", count=True), click.option("-v", "--verbose", count=True))(fn)
    return fn


def process_loglevel(options: Namespace, verbose_flag: bool = False) -> Namespace:
    verbose = options.__dict__.pop("verbose") - options.__dict__.pop("quiet")
    level = max(min(verbose, 1), -1)

    # console = Console(theme=Theme({"log.time": "cyan"}))
    logging.basicConfig(
        level={-1: logging.WARNING, 0: logging.INFO, 1: logging.DEBUG}[level],
        # datefmt="[%X]",
        # handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )

    options.verbose = verbose
    return options


CLICKWRAPPERS: dict[str, tuple[AddArgFn | None, ProcessOptionsFn | None]] = {
    "default": (add_loglevel, process_loglevel),
}


def validate_add_argument_function(wrapper: AddArgFn, fn: MainFn) -> MainFn:
    fn1 = wrapper(fn)
    if not callable(fn1):
        raise RuntimeError(f"wrapper function {wrapper} doesn't return a callable")
    return fn1


def clickwrapper(
    add_arguments: AddArgFn | Sequence[AddArgFn] | None = None,
    process_options: ProcessOptionsFn | Sequence[ProcessOptionsFn] | None = None,
) -> Callable[[MainFn], None]:
    def _clickwrapper(fn: MainFn):
        if add_arguments:
            wrappers = add_arguments if isinstance(add_arguments, Sequence) else [add_arguments]
            for wrapper in wrappers:
                fn = validate_add_argument_function(wrapper, fn)

        @functools.wraps(fn)
        def __clickwrapper(*args, **kwargs):
            options = Namespace(**kwargs)
            if process_options:
                processors = process_options if isinstance(process_options, Sequence) else [process_options]
                for process in processors:
                    options = process(options) or options

            if hasattr(options, "error"):
                raise RuntimeError("you have an error option")

            def error(msg):
                raise click.UsageError(msg)

            options.error = error
            if ret := fn(options):
                raise click.exceptions.Exit(ret)
            return ret

        return __clickwrapper

    return _clickwrapper


def clickwrap(
    kind: str | None = "default", add_arguments: AddArgFn | None = None, process_options: ProcessOptionsFn | None = None
) -> Callable[[MainFn], Any]:
    args0: list[AddArgFn] = []
    args1: list[ProcessOptionsFn] = []
    if kind:
        if kind not in CLICKWRAPPERS:
            raise RuntimeError(f"cannot find CLICKWRAPPERS[{kind}]")
        if arg := CLICKWRAPPERS[kind][0]:
            args0.append(arg)
        if arg1 := CLICKWRAPPERS[kind][1]:
            args1.append(arg1)
    if add_arguments:
        args0.append(add_arguments)
    if process_options:
        args1.append(process_options)
    return clickwrapper(args0, args1)


def command():
    return cloup.command(
        formatter_settings=cloup.HelpFormatter.settings(theme=cloup.HelpTheme.dark()), context_settings={"show_default": True}
    )


def group():
    return cloup.group(formatter_settings=cloup.HelpFormatter.settings(theme=cloup.HelpTheme.dark()), show_subcommand_aliases=True)


if __name__ == "__main__":
    log = logging.getLogger(__name__)

    # @cloup.command(formatter_settings=cloup.HelpFormatter.settings(theme=cloup.HelpTheme.dark()))
    @command()
    @clickwrap("default")
    def main(args: Namespace) -> int:
        log.debug("a debug message")
        log.info("an info message, got verbose=%i", args.verbose)
        log.warning("a warning message")
        return 1

    main()
