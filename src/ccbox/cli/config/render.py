"""``ccbox render`` -- print the generated .claude/settings.json."""

import argparse
import json

from ...claude_settings import render_settings
from ...config import load_config
from ..base import Command


class RenderCommand(Command):
    """Print the generated ``.claude/settings.json`` as JSON."""

    name = "render"
    help = "show the generated .claude/settings.json"
    category = "config"

    def run(self, args: argparse.Namespace) -> int:
        print(json.dumps(render_settings(load_config(args.project_dir)), indent=2))
        return 0
