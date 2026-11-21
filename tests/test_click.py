import inspect
from textwrap import dedent

import pytest
from click.testing import CliRunner

from acbox import utils


def _(txt: str, strip: bool = True) -> str:
    out = dedent(txt)
    ret = f"\n{out}\n"
    return ret[:-1] if (strip and ret.endswith("\n\n")) else ret


@pytest.fixture(scope="function")
def runner(resolver):
    mod = utils.loadmod(resolver.lookup("cli/test.py"))
    main = mod.main

    def invoke(*args, **kwargs):
        runner = CliRunner()
        ret = runner.invoke(main, *args, **kwargs)
        return _(ret.output, strip=True)

    return invoke


def test_internals(resolver):
    mod = utils.loadmod(resolver.lookup("cli/test.py"))
    main, option0, option1, option2 = (
        mod.main,
        mod.option0,
        mod.option1,
        mod.option2,
    )

    assert """
@options()
def option0(fn: MainFn) -> MainFn:
    "the doubler"
    return click.option("--doubler", is_flag=True)(fn)
""" == _(inspect.getsource(option0.fn))
    assert option0.fn is option0.wrapped.fn
    assert "the doubler" == option0.wrapped.fn.__doc__

    assert """
@option0.contextmanager
def option0_context(options: ArgsType) -> Generator[Callable, None, None]:
    "doubling action"

    def doubler(ret: int) -> int:
        if options.doubler or options.x == 8:
            print(f"AFTER DOUBLING -> {ret * 2}")
            return ret * 2
        return ret

    yield doubler
""" == _(inspect.getsource(option0.with_context))
    assert option0.with_context.__wrapped__ is option0.wrapped.context
    assert "doubling action" == option0.with_context.__doc__

    assert """
@options()
def option1(fn: MainFn) -> MainFn:
    "option1 doctext"
    return click.option("-x", type=int)(fn)
""" == _(inspect.getsource(option1.fn))
    assert option1.fn is option1.wrapped.fn
    assert "option1 doctext" == option1.fn.__doc__

    assert """
@option1.process
def process(args: ArgsType) -> None:
    "option1 process doctext"
    args.x = args.x or 0
""" == _(inspect.getsource(option1.process_options.fn))
    assert option1.process_options.fn is option1.wrapped.process
    assert "option1 process doctext" == option1.process_options.fn.__doc__

    assert """
@options()
def option2(fn: MainFn) -> MainFn:
    "option2 doctext"
    return click.option("-y", type=int)(fn)
""" == _(inspect.getsource(option2.fn))
    assert option2.fn is option2.wrapped.fn
    assert "option2 doctext" == option2.fn.__doc__

    assert """
@option2.process  # type: ignore[no-redef]
def process(args: ArgsType) -> ArgsType:  # noqa: F811
    "option2 process doctext"
    args.y = args.y or 0
    return args
""" == _(inspect.getsource(option2.process_options.fn))
    assert option2.process_options.fn is option2.wrapped.process
    assert "option2 process doctext" == option2.process_options.fn.__doc__

    assert """
@command(options=[option0, option1, option2])
def main(args: ArgsType) -> int:
    "hi there"
    print(f"Got for x {args.x}")
    print(f"Got for y {args.y}")
    return args.x + args.y
""" == _(inspect.getsource(main.fn))
    assert "hi there" == main.__doc__

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert """
Usage: main [OPTIONS]

  hi there

Options:
  --doubler
  -x INTEGER
  -y INTEGER
  --help      Show this message and exit.
""" == _(result.output)


def test_execution(runner):
    assert """
Got for x 11
Got for y 0
""" == runner(["-x", "11"])

    assert """
Got for x 9
Got for y 11
""" == runner(["-x", "9", "-y", "11"])

    assert """
Got for x 8
Got for y 12
AFTER DOUBLING -> 40
""" == runner(["--doubler", "-x", "8", "-y", "12"])
