"""``ccbox init`` -- scaffold a project .ccbox.yaml."""

import argparse
import sys
from pathlib import Path

from ccbox.cli.base import Command
from ccbox.config import PROJECT_CONFIG_FILENAME

INIT_TEMPLATE = """\
# ccbox project configuration. Merged over the global config.
mode: accident          # accident | adversarial
runtime: auto           # auto-detect; or docker | podman | podman-hpc | apptainer | singularity

# image: registry.example/dev@sha256:...   # pin by digest for reproducibility

mounts:
  # - { src: $CONDA_PREFIX, mode: ro, same_path: true }
  # - { src: ./data, dst: /data, mode: rw }

env:
  # - PATH=$CONDA_PREFIX/bin:$PATH

claude:
  deny: []
    # - Read(/path/code/should/reach/but/claude/should/not/**)
"""


class InitCommand(Command):
    """Write a starter ``.ccbox.yaml`` in the project directory."""

    name = "init"
    help = "scaffold a .ccbox.yaml"
    category = "config"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--force", action="store_true", help="overwrite an existing file"
        )

    def run(self, args: argparse.Namespace) -> int:
        """Write the template, refusing to overwrite unless ``--force`` is set."""
        target = Path(args.project_dir) / PROJECT_CONFIG_FILENAME
        if target.exists() and not args.force:
            print(
                f"{target} already exists (use --force to overwrite)", file=sys.stderr
            )
            return 1
        target.write_text(INIT_TEMPLATE, encoding="utf-8")
        print(f"wrote {target}")
        return 0
