"""Base class shared by all CLI commands.

Commands register themselves simply by subclassing :class:`Command` with a
non-empty :attr:`name`: :meth:`Command.__init_subclass__` records each one, so
no central list needs editing. :mod:`ccbox.cli.registry` imports every command
module to trigger these registrations and then exposes the collected commands.
"""

from __future__ import annotations

import abc
import argparse

_REGISTRY: list[type[Command]] = []


class Command(abc.ABC):
    """One ``ccbox <name>`` subcommand.

    Subclasses set :attr:`name`, :attr:`help` and :attr:`category`, optionally
    override :meth:`add_arguments`, and implement :meth:`run`. Defining a
    subclass with a non-empty :attr:`name` registers it automatically; abstract
    intermediate bases (no ``name``) are skipped.
    """

    name: str = ""
    help: str = ""
    category: str = ""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.name:
            _REGISTRY.append(cls)

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Register subcommand-specific arguments (no-op by default)."""

    @abc.abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Execute the command and return a process exit code."""
        raise NotImplementedError


def registered_commands() -> list[type[Command]]:
    """Return every registered command class, in definition order."""
    return list(_REGISTRY)
