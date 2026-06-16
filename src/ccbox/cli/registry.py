"""Aggregate commands from every category package.

To add a command: create a module in the right category package and append its
class to that package's ``COMMANDS``. To add a category: create a package with a
``COMMANDS`` list and register it in :data:`COMMAND_GROUPS` below.
"""

from __future__ import annotations

from typing import Dict, List, Type

from ccbox.cli.base import Command
from ccbox.cli.config import COMMANDS as CONFIG_COMMANDS
from ccbox.cli.diagnostics import COMMANDS as DIAGNOSTICS_COMMANDS
from ccbox.cli.sandbox import COMMANDS as SANDBOX_COMMANDS
from ccbox.cli.sync import COMMANDS as SYNC_COMMANDS

COMMAND_GROUPS: Dict[str, List[Type[Command]]] = {
    "config": CONFIG_COMMANDS,
    "sandbox": SANDBOX_COMMANDS,
    "diagnostics": DIAGNOSTICS_COMMANDS,
    "sync": SYNC_COMMANDS,
}

ALL_COMMANDS: List[Type[Command]] = [
    command for group in COMMAND_GROUPS.values() for command in group
]
