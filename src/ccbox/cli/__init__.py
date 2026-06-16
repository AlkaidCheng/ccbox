"""ccbox command-line interface.

The CLI is a thin dispatcher. Commands live in purpose-based subpackages
(``config``, ``sandbox``, ``diagnostics``, ...), each exposing a ``COMMANDS``
list that :mod:`ccbox.cli.registry` aggregates. ``ccbox.cli:main`` is the
console-script entry point declared in pyproject.toml.
"""

from ccbox.cli.main import build_parser, main

__all__ = ["build_parser", "main"]
