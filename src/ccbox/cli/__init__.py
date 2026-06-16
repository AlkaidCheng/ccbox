"""ccbox command-line interface.

The CLI is a thin dispatcher. Commands live in purpose-based subpackages
(``config``, ``sandbox``, ``diagnostics``, ...) and register themselves by
subclassing :class:`~ccbox.cli.base.Command`; :mod:`ccbox.cli.registry`
imports the subpackages and collects the registrations. ``ccbox.cli:main`` is
the console-script entry point declared in pyproject.toml.
"""

from ccbox.cli.main import build_parser, main

__all__ = ["build_parser", "main"]
