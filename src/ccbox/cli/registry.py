"""Aggregate every CLI command.

Commands register themselves by subclassing :class:`~ccbox.cli.base.Command`
(see :meth:`Command.__init_subclass__`). Importing the category packages below
runs those subclass definitions; :data:`ALL_COMMANDS` then exposes the collected
commands sorted by category and name. Adding a command to an existing category
needs no edit here -- it registers when its category package imports it. A
brand-new category needs one import line below.
"""

from __future__ import annotations

from typing import Dict, List, Type

# Imported for their registration side effects: importing each category package
# defines its Command subclasses, which self-register via __init_subclass__.
from ccbox.cli import config, diagnostics, image, sandbox, sync  # noqa: F401
from ccbox.cli.base import Command, registered_commands

ALL_COMMANDS: List[Type[Command]] = sorted(
    registered_commands(), key=lambda command: (command.category, command.name)
)

COMMAND_GROUPS: Dict[str, List[Type[Command]]] = {}
for _command in ALL_COMMANDS:
    COMMAND_GROUPS.setdefault(_command.category, []).append(_command)
