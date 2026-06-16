"""``ccbox pull`` -- pull the configured image URL into the local cache."""

import argparse
import subprocess
from pathlib import Path

from ccbox.cli.base import Command
from ccbox.config import load_config
from ccbox.image import image_kind, validate
from ccbox.image_pull import SIF_PULL_RUNTIMES, pull_image_command, sif_filename
from ccbox.log import logger
from ccbox.runtime import get_runtime, resolve_runtime
from ccbox.sandbox import cache_dir


class PullCommand(Command):
    """Pull the configured image URL with the resolved runtime and cache it.

    OCI runtimes pull into their local image store; Apptainer/Singularity pull
    a ``.sif`` into the ccbox cache, reused on later runs.
    """

    name = "pull"
    help = "pull the configured image URL into the local cache"
    category = "image"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="print the pull command without running it",
        )

    def run(self, args: argparse.Namespace) -> int:
        config = load_config(args.project_dir)
        image = config.get("image")
        if not image:
            logger.error("pull needs an 'image' URL in config")
            return 1
        if image_kind(image) != "url":
            logger.error(
                "pull needs an image URL (got %r); use a scheme like docker://", image
            )
            return 1
        try:
            runtime = resolve_runtime(config)
        except (RuntimeError, ValueError) as exc:
            logger.error("%s", exc)
            return 1
        if validate(image, runtime) == "incompatible":
            logger.error("runtime %r cannot pull image URLs", runtime)
            return 1
        backend = get_runtime(runtime)
        sif_path = None
        if runtime in SIF_PULL_RUNTIMES:
            sif_path = str(cache_dir() / "images" / sif_filename(image))
        try:
            command = pull_image_command(runtime, backend.binary, image, sif_path)
        except ValueError as exc:
            logger.error("%s", exc)
            return 1
        if args.dry_run:
            print(" ".join(command))
            return 0
        if not backend.available():
            logger.error("runtime %r not found on PATH", runtime)
            return 1
        if sif_path:
            dest = Path(sif_path)
            if dest.exists():
                logger.info("using cached image %s", dest)
                return 0
            dest.parent.mkdir(parents=True, exist_ok=True)
            logger.info("pulling %s -> %s", image, dest)
        else:
            logger.info("pulling %s into the %s image store", image, runtime)
        return subprocess.run(command, check=False).returncode
