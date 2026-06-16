"""Adversarial-mode git sync commands."""

from ccbox.cli.base import Command
from ccbox.cli.sync.apply import ApplyCommand
from ccbox.cli.sync.harvest import HarvestCommand

COMMANDS: list[type[Command]] = [HarvestCommand, ApplyCommand]
