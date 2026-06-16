"""``ccbox bake`` -- build the OCI image from the build recipe (a Dockerfile)."""

import argparse
import subprocess
import sys
from pathlib import Path

from ccbox.cli.base import Command
from ccbox.config import load_config
from ccbox.image import validate
from ccbox.image_build import OCI_BUILDERS, build_image_command, detect_builder


class BakeCommand(Command):
    """Build an OCI image from the configured Dockerfile recipe.

    The image is the universal artifact: OCI runtimes use it directly, while
    Apptainer/Singularity and Shifter consume it via conversion or pull.
    """

    name = "bake"
    help = "build the OCI image from the build recipe (a Dockerfile)"
    category = "image"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the build command without running it",
        )

    def run(self, args: argparse.Namespace) -> int:
        config = load_config(args.project_dir)
        build = config.get("build") or {}
        recipe = build.get("recipe")
        image = config.get("image")
        if not recipe:
            print(
                "[error] bake needs 'build.recipe' (a Dockerfile path) in config",
                file=sys.stderr,
            )
            return 1
        if not image:
            print("[error] bake needs an 'image' tag in config", file=sys.stderr)
            return 1
        runtime = config.get("runtime", "auto")
        if runtime != "auto" and validate(image, runtime) == "incompatible":
            print(
                f"[error] runtime {runtime!r} cannot use a built OCI image",
                file=sys.stderr,
            )
            return 1
        builder = build.get("builder") or detect_builder()
        if not builder:
            print(
                f"[error] no OCI image builder found on PATH (looked for: {', '.join(OCI_BUILDERS)})",
                file=sys.stderr,
            )
            return 1
        recipe_path = str(Path(args.project_dir) / recipe)
        command = build_image_command(
            builder, image, recipe_path, str(args.project_dir)
        )
        if args.dry_run:
            print(" ".join(command))
            return 0
        return subprocess.run(command, check=False).returncode
