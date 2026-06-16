"""``ccbox doctor`` -- static safety checks on the effective config."""

import argparse

from ...config import load_config
from ...doctor import check
from ..base import Command


class DoctorCommand(Command):
    """Print configuration issues and exit non-zero on any error."""

    name = "doctor"
    help = "check the config for safety issues"
    category = "diagnostics"

    def run(self, args: argparse.Namespace) -> int:
        issues = check(load_config(args.project_dir))
        for issue in issues:
            print(f"[{issue.level}] {issue.message}")
        if not issues:
            print("ok: no issues found")
        return 1 if any(issue.level == "error" for issue in issues) else 0
