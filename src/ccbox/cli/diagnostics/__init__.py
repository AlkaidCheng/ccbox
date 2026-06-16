"""Environment & safety inspection commands."""

from ..base import Command
from .doctor import DoctorCommand
from .runtimes import RuntimesCommand

COMMANDS: list[type[Command]] = [DoctorCommand, RuntimesCommand]
