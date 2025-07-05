from __future__ import annotations

import argparse
import types

from ..flags.base import ArgumentTypeBase
from ..shared import ArgsCallback, check_default_constructor


class ArgumentParserBase(argparse.ArgumentParser):
    def __init__(self, modules: list[types.ModuleType], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.modules = modules
        self.callbacks: list[ArgsCallback | None] = []

    def _post_process(self, options):
        for name in dir(options):
            if isinstance(getattr(options, name), ArgumentTypeBase):
                fallback = getattr(options, name).value
                setattr(
                    options,
                    name,
                    None if fallback is ArgumentTypeBase._NA else fallback,
                )
        for callback in self.callbacks:
            options = callback(options) or options
        return options

    def parse_known_args(self, args=None, namespace=None):
        options, argv = super().parse_known_args(args, namespace)
        return self._post_process(options), argv

    def parse_args(self, args=None, namespace=None):
        options = super().parse_args(args, namespace)
        for name in dir(options):
            if isinstance(getattr(options, name), ArgumentTypeBase):
                fallback = getattr(options, name).value
                setattr(
                    options,
                    name,
                    None if fallback is ArgumentTypeBase._NA else fallback,
                )
        return options

    def add_argument(self, *args, **kwargs):
        typ = kwargs.get("type")
        obj = None
        if isinstance(typ, type) and issubclass(typ, ArgumentTypeBase):
            check_default_constructor(typ)
            obj = typ()
        if isinstance(typ, ArgumentTypeBase):
            obj = typ
        if obj is not None:
            obj.default = kwargs.get("default", ArgumentTypeBase._NA)
            kwargs["default"] = obj
            kwargs["type"] = obj
        super().add_argument(*args, **kwargs)

    def error(self, message):
        try:
            super().error(message)
        except SystemExit:
            # gh-121018
            raise argparse.ArgumentError(None, message)

    @classmethod
    def get_parser(cls, modules: list[types.ModuleType], **kwargs):
        raise NotImplementedError("implement this method")
