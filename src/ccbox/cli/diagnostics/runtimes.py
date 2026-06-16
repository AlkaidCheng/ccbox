"""``ccbox runtimes`` -- list backends and the auto-detected default."""

import argparse

from ccbox.cli.base import Command
from ccbox.runtime import REGISTRY, detect_runtime


class RuntimesCommand(Command):
    """List backends with availability and the auto-detected default."""

    name = "runtimes"
    help = "list backends and the auto-detected default"
    category = "diagnostics"

    def run(self, args: argparse.Namespace) -> int:
        chosen = detect_runtime()
        for name, backend in REGISTRY.items():
            mark = "*" if name == chosen else " "
            status = "available" if backend.available() else "-"
            note = "" if backend.implemented else "(not implemented)"
            print(f"{mark} {name:12} {status:10} {note}")
        print(f"\nauto -> {chosen or 'none found'}")
        return 0
