import subprocess
import sys

import pytest


@pytest.fixture(scope="function")
def examples(resolver):
    yield lambda path: resolver.lookup(resolver.root.parent.parent / path)


@pytest.fixture(scope="function")
def runner(resolver):
    def run(example, args=None):
        script = resolver.lookup(resolver.root.parent.parent / example)
        p = subprocess.Popen(
            [sys.executable, str(script), *[str(c) for c in (args or [])]], encoding="utf-8", stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )
        out, err = p.communicate()
        return p.returncode, out, err

    yield run


def test_single_command_help(runner):
    code, out, err = runner("docs/examples/single-command.py", ["--help"])
    assert (
        """\
usage: single-command.py [-h] [-v] [-q]

options:
  -h, --help     show this help message and exit

Logging:
  Logging related options

  -v, --verbose  report verbose logging (default: None)
  -q, --quiet    report quiet logging (default: None)
"""
        == out
    )


@pytest.mark.skip(reason="broken")
def test_single_command_run(runner):
    code, out, err = runner("docs/examples/single-command.py")
    assert not code
    assert (
        """\
args:
  .error: (callable) abort a script with an error message
  .modules: (<class 'list'>)
     <module 'acbox.cli.script' from '/Users/antonio/Projects/github/acbox/src/acbox/cli/script.py'>
     <module '__main__' from '/Users/antonio/Projects/github/acbox/docs/examples/single-command.py'>
"""
        == out
    )

    assert (
        """\
INFO:__main__:an info message, you can silence it with -q|--quiet
WARNING:__main__:a warning!
"""
        == err
    )
