"""Sandbox lifecycle commands."""

from ccbox.cli.base import Command
from ccbox.cli.sandbox.enter import EnterCommand

COMMANDS: list[type[Command]] = [EnterCommand]
