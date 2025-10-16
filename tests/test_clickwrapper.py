from argparse import Namespace

import click
from click.testing import CliRunner

from acbox import clickwrapper


def test_base():
    @click.command()
    @clickwrapper.clickwrap()
    def main(args: Namespace) -> None:
        pass

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert (
        """
Usage: main [OPTIONS]

Options:
  -q, --quiet
  -v, --verbose
  --help         Show this message and exit.
""".lstrip()
        == result.stdout
    )
