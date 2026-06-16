"""Image management commands."""

from ccbox.cli.base import Command
from ccbox.cli.image.bake import BakeCommand

COMMANDS: list[type[Command]] = [BakeCommand]
