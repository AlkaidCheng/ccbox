"""``ccbox enter`` -- launch Claude Code (or a command) inside the sandbox."""

import argparse
import sys

from ...config import load_config
from ...doctor import check
from ...runtime import get_runtime, resolve_runtime
from ..base import Command


class EnterCommand(Command):
    """Resolve the runtime and print the sandbox invocation (dry run)."""

    name = "enter"
    help = "enter the sandbox (dry run for now)"
    category = "sandbox"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("argv", nargs="*", help="command to run inside the sandbox")

    def run(self, args: argparse.Namespace) -> int:
        config = load_config(args.project_dir)
        errors = [issue for issue in check(config) if issue.level == "error"]
        if errors:
            for issue in errors:
                print(f"[error] {issue.message}", file=sys.stderr)
            print("refusing to enter: fix doctor errors first", file=sys.stderr)
            return 1
        try:
            name = resolve_runtime(config)
        except (RuntimeError, ValueError) as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 1
        command = get_runtime(name).build_run_command(config, args.argv or ["bash"])
        print(f"# runtime: {name}")
        print(" ".join(command))
        print("(dry run: live execution wiring lands in Phase 1)")
        return 0
