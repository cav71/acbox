import typing as t
from click.core import Command

# .venv/lib/python3.13/site-packages/click/decorators.py
# .venv/lib/python3.13/site-packages/click/core.py
_AnyCallable = t.Callable[..., t.Any]


def command(*args: t.Any, **kwargs: t.Any) -> t.Callable[[t.Callable[..., t.Any]], Command] | Command:
