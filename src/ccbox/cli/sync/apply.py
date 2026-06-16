"""``ccbox apply`` -- apply a reviewed git bundle into the host repo."""

import argparse
import sys

from ccbox.cli.base import Command
from ccbox.config import load_config
from ccbox.git_sync import DEFAULT_BUNDLE_NAME, apply
from ccbox.sandbox import adversarial_workspace


class ApplyCommand(Command):
    """Fetch a branch from a reviewed bundle into the host repo.

    In adversarial mode the bundle defaults to the one harvested into the
    outbox; otherwise a bundle path must be given.
    """

    name = "apply"
    help = "apply a git bundle into the host repo"
    category = "sync"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "bundle",
            nargs="?",
            default=None,
            help="bundle file (default: the adversarial outbox bundle)",
        )
        parser.add_argument(
            "branch", nargs="?", default="HEAD", help="ref to fetch (default: HEAD)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the command without running it",
        )

    def run(self, args: argparse.Namespace) -> int:
        bundle = args.bundle
        if bundle is None:
            config = load_config(args.project_dir)
            if config.get("mode") != "adversarial":
                print("error: a bundle file is required", file=sys.stderr)
                return 1
            _, outbox_dir = adversarial_workspace(args.project_dir)
            bundle = str(outbox_dir / DEFAULT_BUNDLE_NAME)
        return apply(
            bundle, args.branch, repo_dir=str(args.project_dir), dry_run=args.dry_run
        )
