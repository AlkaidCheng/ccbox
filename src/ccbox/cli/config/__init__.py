"""Configuration & scaffolding commands."""

from ccbox.cli.base import Command
from ccbox.cli.config.init import InitCommand
from ccbox.cli.config.render import RenderCommand
from ccbox.cli.config.show import ShowConfigCommand

COMMANDS: list[type[Command]] = [InitCommand, ShowConfigCommand, RenderCommand]
