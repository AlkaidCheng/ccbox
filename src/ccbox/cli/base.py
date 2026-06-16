"""Base class shared by all CLI commands."""

import abc
import argparse


class Command(abc.ABC):
    """One ``ccbox <name>`` subcommand.

    Subclasses set :attr:`name`, :attr:`help` and :attr:`category`, optionally
    override :meth:`add_arguments`, and implement :meth:`run`.
    """

    name: str = ""
    help: str = ""
    category: str = ""

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Register subcommand-specific arguments (no-op by default)."""

    @abc.abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        """Execute the command and return a process exit code."""
        raise NotImplementedError
