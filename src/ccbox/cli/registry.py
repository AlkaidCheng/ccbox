"""Aggregate commands from every category package.

To add a command: create a module in the right category package and append its
class to that package's ``COMMANDS``. To add a category: create a package with a
``COMMANDS`` list and register it in :data:`COMMAND_GROUPS` below.
"""

from __future__ import annotations

from typing import Dict, List, Type

from .base import Command
from .config import COMMANDS as CONFIG_COMMANDS
from .diagnostics import COMMANDS as DIAGNOSTICS_COMMANDS
from .sandbox import COMMANDS as SANDBOX_COMMANDS

COMMAND_GROUPS: Dict[str, List[Type[Command]]] = {
    "config": CONFIG_COMMANDS,
    "sandbox": SANDBOX_COMMANDS,
    "diagnostics": DIAGNOSTICS_COMMANDS,
}

ALL_COMMANDS: List[Type[Command]] = [
    command for group in COMMAND_GROUPS.values() for command in group
]
