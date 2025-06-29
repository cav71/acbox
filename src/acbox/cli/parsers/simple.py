import argparse
import logging
import sys
import types

from .base import ArgumentParserBase

log = logging.getLogger(__name__)


def log_sys_info(modules: list[types.ModuleType]):
    log.debug("interpreter: %s", sys.executable)


class ArgumentParser(ArgumentParserBase):
    def parse_args(self, args=None, namespace=None):
        options = super().parse_args(args, namespace)

        # reserver attributes
        for reserved in [
            "modules",
            "error",
        ]:
            if not hasattr(options, reserved):
                continue
            raise RuntimeError(f"cannot add an argument with dest='{reserved}'")
        options.error = self.error
        options.modules = self.modules

        for callback in self.callbacks:
            if not callback:
                continue
            options = callback(options) or options

        log_sys_info(self.modules)
        return options

    @classmethod
    def get_parser(cls, modules: list[types.ModuleType], **kwargs):
        class Formatter(
            argparse.RawTextHelpFormatter,
            argparse.RawDescriptionHelpFormatter,
            argparse.ArgumentDefaultsHelpFormatter,
        ):
            pass

        return cls(modules, formatter_class=Formatter, **kwargs)
