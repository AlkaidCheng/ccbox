"""``ccbox harvest`` -- export a branch as a reviewable git bundle."""

import argparse

from ccbox.cli.base import Command
from ccbox.git_sync import harvest


class HarvestCommand(Command):
    """Bundle a branch into a file for review and apply elsewhere."""

    name = "harvest"
    help = "export a branch as a git bundle"
    category = "sync"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "branch", nargs="?", default="HEAD", help="ref to bundle (default: HEAD)"
        )
        parser.add_argument(
            "--out", default="ccbox-harvest.bundle", help="output bundle path"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the command without running it",
        )

    def run(self, args: argparse.Namespace) -> int:
        return harvest(
            args.branch, args.out, repo_dir=args.project_dir, dry_run=args.dry_run
        )
