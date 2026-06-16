"""``ccbox enter`` -- launch Claude Code (or a command) inside the sandbox."""

import argparse
import sys

from ...config import load_config
from ...doctor import check
from ...sandbox import enter
from ..base import Command


class EnterCommand(Command):
    """Launch Claude Code (or a given command) inside the sandbox."""

    name = "enter"
    help = "launch the sandbox for the project"
    category = "sandbox"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the sandbox command without writing settings or running it",
        )
        parser.add_argument("argv", nargs="*", help="command to run inside the sandbox")

    def run(self, args: argparse.Namespace) -> int:
        config = load_config(args.project_dir)
        errors = [issue for issue in check(config) if issue.level == "error"]
        if errors:
            for issue in errors:
                print(f"[error] {issue.message}", file=sys.stderr)
            print("refusing to enter: fix doctor errors first", file=sys.stderr)
            return 1
        try:
            return enter(config, args.project_dir, args.argv, dry_run=args.dry_run)
        except (RuntimeError, ValueError) as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 1
