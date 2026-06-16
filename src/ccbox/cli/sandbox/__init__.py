"""Sandbox lifecycle commands."""

from ..base import Command
from .enter import EnterCommand

COMMANDS: list[type[Command]] = [EnterCommand]
