"""``ccbox apply`` -- apply a reviewed git bundle into the host repo."""

import argparse

from ccbox.cli.base import Command
from ccbox.git_sync import apply


class ApplyCommand(Command):
    """Fetch a branch from a reviewed bundle into the host repo."""

    name = "apply"
    help = "apply a git bundle into the host repo"
    category = "sync"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("bundle", help="bundle file to apply")
        parser.add_argument(
            "branch", nargs="?", default="HEAD", help="ref to fetch (default: HEAD)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the command without running it",
        )

    def run(self, args: argparse.Namespace) -> int:
        return apply(
            args.bundle, args.branch, repo_dir=args.project_dir, dry_run=args.dry_run
        )
