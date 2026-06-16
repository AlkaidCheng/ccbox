"""``ccbox enter`` -- launch Claude Code (or a command) inside the sandbox."""

import argparse

from ccbox.cli.base import Command
from ccbox.config import load_config
from ccbox.doctor import check
from ccbox.log import logger
from ccbox.sandbox import enter


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
        parser.add_argument(
            "--warm",
            action="store_true",
            help="reuse a persistent named container for fast re-entry",
        )
        parser.add_argument("argv", nargs="*", help="command to run inside the sandbox")

    def run(self, args: argparse.Namespace) -> int:
        config = load_config(args.project_dir)
        errors = [issue for issue in check(config) if issue.level == "error"]
        if errors:
            for issue in errors:
                logger.error(issue.message)
            logger.error("refusing to enter: fix doctor errors first")
            return 1
        try:
            return enter(
                config,
                args.project_dir,
                args.argv,
                dry_run=args.dry_run,
                warm=args.warm,
            )
        except (RuntimeError, ValueError) as exc:
            logger.error("%s", exc)
            return 1
