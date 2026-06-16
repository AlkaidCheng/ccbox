"""``ccbox config`` -- print the merged effective configuration."""

import argparse
import json

from ccbox.cli.base import Command
from ccbox.config import load_config


class ShowConfigCommand(Command):
    """Print the merged effective configuration as JSON."""

    name = "config"
    help = "show the merged effective config"
    category = "config"

    def run(self, args: argparse.Namespace) -> int:
        print(json.dumps(load_config(args.project_dir), indent=2))
        return 0
