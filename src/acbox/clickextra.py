from __future__ import annotations

import contextlib
import dataclasses as dc
import inspect
from argparse import Namespace
from collections.abc import Callable
from typing import Any, TypeAlias

ArgsType: TypeAlias = Namespace
MainFn = Callable[[ArgsType], Any]
OptionsFn = Callable[[ArgsType], ArgsType | None]


REGISTRY: dict[str, Options] = {}


@dc.dataclass
class Wrapped:
    fn: Callable | None = None
    process: Callable[[ArgsType], ArgsType | None] | None = None
    context: Callable[[ArgsType], ArgsType | None] | None = None


@dc.dataclass
class Options:
    fn: Callable
    process_options: Callable | None = None
    with_context: Callable | None = None
    key: str | None = None
    wrapped: Wrapped = dc.field(default_factory=Wrapped)

    def __post_init__(self):
        assert self.fn
        self.wrapped = Wrapped(self.fn)

    def __repr__(self):
        tag = f" register='{self.key}'" if self.key else ""
        return f"<{self.__class__.__name__} fn={self.fn}{tag}>"

    def __call__(self, fn: Callable | None = None) -> Any:
        if not (ret := self.fn(fn)):
            module = inspect.getmodule(self.fn) or None
            loc = f"{module and module.__file__ or 'N/A'}:{inspect.getsourcelines(self.fn)[1]}"
            raise RuntimeError(f"None returning function '{self.fn.__name__}' in {loc}")
        return ret

    def process(self, fn: OptionsFn) -> OptionsFn:
        @dc.dataclass
        class X:
            fn: Callable

            def __call__(self, *args, **kwargs):
                return self.fn(*args, **kwargs)

        self.wrapped.process = fn
        self.process_options = X(fn)
        return fn

    def contextmanager(self, fn: OptionsFn) -> OptionsFn:
        self.wrapped.context = fn
        self.with_context = contextlib.contextmanager(fn)  # type: ignore[arg-type]
        return fn


def options(register=None):
    def _fn(fn: OptionsFn) -> Options:
        out = Options(fn)
        if register:
            if register in REGISTRY:
                raise RuntimeError(f"option '{register}' already registered")

            out.key = register
            REGISTRY[register] = out
        return out

    return _fn


def parse_options_argument(options: list[Options | str]) -> list[Options]:
    alloptions = []
    for item in reversed(options):
        if isinstance(item, Options):
            option = item
        elif isinstance(item, str):
            if item not in REGISTRY:
                raise RuntimeError(f"cannot find registered options '{item}' in REGISTRY")
            option = REGISTRY[item]
        else:
            raise TypeError(f"cannot handle option '{item}'")
        if option not in alloptions:
            alloptions.append(option)
    return alloptions
