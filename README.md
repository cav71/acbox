## ACBox my little toolbox

[![PyPI version](https://img.shields.io/pypi/v/acbox.svg?color=blue)](https://pypi.org/project/acbox)
[![Python versions](https://img.shields.io/pypi/pyversions/acbox.svg)](https://pypi.org/project/acbox)
[![Codecov (main)](https://img.shields.io/codecov/c/github/cav71/acbox/main)](https://app.codecov.io/gh/cav71/acbox/tree/main)
[![Build](https://github.com/cav71/acbox/actions/workflows/main.yml/badge.svg)](https://github.com/cav71/acbox/actions/workflows/main.yml)


[![License - MIT](https://img.shields.io/badge/license-MIT-9400d3.svg)](https://spdx.org/licenses/)
![PyPI - Downloads](https://img.shields.io/pypi/dm/acbox)
[![Mypy](https://img.shields.io/badge/types-Mypy-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


## Quickstart

```
pip install acbox
```

### Helpers

#### cli helper
A cli wrapper modeled after click
```python
from argparse import Namespace
from acbox import clickwrapper

@clickwrapper.command("fancy")
def main(args: Namespace) -> None:
    print(args)
```

#### utilities

A cli runner with verbose output
```python
from acbox.runner import Runner

runner = Runner(True, exe=["git"])
print(runner.run(["status"], capture=True))
```

A loadmod function to load modules from a file
```python
from acbox.utils import loadmod
print(loadmod(Path("support/builder")))
```


Ref. {{gdata.branch}}@{{gdata.rev}} 
