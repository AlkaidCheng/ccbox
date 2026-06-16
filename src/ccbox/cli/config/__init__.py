"""Configuration & scaffolding commands."""

from ..base import Command
from .init import InitCommand
from .render import RenderCommand
from .show import ShowConfigCommand

COMMANDS: list[type[Command]] = [InitCommand, ShowConfigCommand, RenderCommand]
