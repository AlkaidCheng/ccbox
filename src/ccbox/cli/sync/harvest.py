"""``ccbox harvest`` -- export a branch as a reviewable git bundle."""

import argparse

from ccbox.cli.base import Command
from ccbox.config import load_config
from ccbox.git_sync import DEFAULT_BUNDLE_NAME, harvest
from ccbox.sandbox import adversarial_workspace


class HarvestCommand(Command):
    """Bundle a branch into a file for review and apply elsewhere.

    In adversarial mode the branch is bundled from the isolated work copy into
    the outbox; otherwise it is bundled from the project directory.
    """

    name = "harvest"
    help = "export a branch as a git bundle"
    category = "sync"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "branch", nargs="?", default="HEAD", help="ref to bundle (default: HEAD)"
        )
        parser.add_argument(
            "--out", default=None, help="output bundle path (default depends on mode)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the command without running it",
        )

    def run(self, args: argparse.Namespace) -> int:
        config = load_config(args.project_dir)
        if config.get("mode") == "adversarial":
            work_dir, outbox_dir = adversarial_workspace(args.project_dir)
            repo_dir = str(work_dir)
            out = args.out or str(outbox_dir / DEFAULT_BUNDLE_NAME)
            if not args.dry_run:
                outbox_dir.mkdir(parents=True, exist_ok=True)
        else:
            repo_dir = str(args.project_dir)
            out = args.out or "ccbox-harvest.bundle"
        return harvest(args.branch, out, repo_dir=repo_dir, dry_run=args.dry_run)
