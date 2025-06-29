import argparse
import logging
from typing import Any

from ..parsers.base import ArgumentParserBase


def add_arguments_logging(parser: ArgumentParserBase, baselevel: int = logging.INFO) -> None:
    group = parser.add_argument_group("Logging", "Logging related options")
    group.add_argument("-v", "--verbose", dest="managed-loglevel", action="append_const", const=1, help="report verbose logging")
    group.add_argument("-q", "--quiet", dest="managed-loglevel", action="append_const", const=-1, help="report quiet logging")

    levelmap = [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
        logging.FATAL,
    ]
    if baselevel not in levelmap:
        raise IndexError(f"cannot find level {baselevel} in: {levelmap}")

    def setup_logging(config: dict[str, Any]) -> None:
        logging.basicConfig(**config)

    def callback(args: argparse.Namespace):
        config = {}
        count = levelmap.index(baselevel) - sum(getattr(args, "managed-loglevel") or [0])
        config["level"] = levelmap[min(max(count, 0), len(levelmap) - 1)]
        setup_logging(config)
        delattr(args, "managed-loglevel")

    parser.callbacks.append(callback)
