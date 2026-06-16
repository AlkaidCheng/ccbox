"""Environment & safety inspection commands."""

from ccbox.cli.base import Command
from ccbox.cli.diagnostics.doctor import DoctorCommand
from ccbox.cli.diagnostics.runtimes import RuntimesCommand

COMMANDS: list[type[Command]] = [DoctorCommand, RuntimesCommand]
