"""Export and import work as a git bundle (adversarial-mode sync).

Adversarial mode keeps the host repo and SSH key out of the sandbox. Work is
exported from the sandbox's repo copy as a git *bundle* (``harvest``) and
applied to the host repo only after review (``apply``), with hooks neutralised
so a tampered copy cannot run code on the host during the fetch.
"""

import subprocess
from collections.abc import Callable

Runner = Callable[[list[str]], int]

DEFAULT_BUNDLE_NAME = "harvest.bundle"


def build_bundle_command(
    branch: str, out_path: str, repo_dir: str | None = None
) -> list[str]:
    """Return the command that bundles ``branch`` into ``out_path``.

    Parameters
    ----------
    branch : str
        The ref to bundle (a branch name or ``HEAD``).
    out_path : str
        Destination bundle file.
    repo_dir : str or None, optional
        Run git in this directory (``git -C``) when given.

    Returns
    -------
    list[str]
        The ``git bundle create`` argument vector.
    """
    prefix = ["git", "-C", repo_dir] if repo_dir else ["git"]
    return [*prefix, "bundle", "create", out_path, branch]


def build_apply_command(
    bundle_path: str, branch: str, repo_dir: str | None = None
) -> list[str]:
    """Return the host-side command that fetches ``branch`` from a bundle.

    Hooks are neutralised (``core.hooksPath=/dev/null``) so a tampered bundle
    cannot run code on the host during the fetch.

    Parameters
    ----------
    bundle_path : str
        The bundle file to fetch from.
    branch : str
        The ref to fetch.
    repo_dir : str or None, optional
        Run git in this directory (``git -C``) when given.

    Returns
    -------
    list[str]
        The hardened ``git fetch`` argument vector.
    """
    prefix = ["git", "-C", repo_dir] if repo_dir else ["git"]
    return [*prefix, "-c", "core.hooksPath=/dev/null", "fetch", bundle_path, branch]


def _subprocess_runner(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def harvest(
    branch: str,
    out_path: str,
    *,
    repo_dir: str | None = None,
    dry_run: bool = False,
    runner: Runner = _subprocess_runner,
) -> int:
    """Bundle ``branch`` into ``out_path``.

    Parameters
    ----------
    branch : str
        The ref to bundle.
    out_path : str
        Destination bundle file.
    repo_dir : str or None, keyword-only, optional
        The repository to bundle from.
    dry_run : bool, keyword-only, optional
        When True, print the command instead of running it.
    runner : callable, keyword-only, optional
        Executes the command and returns an exit code. Injectable for testing.

    Returns
    -------
    int
        The exit code (0 for a dry run).
    """
    command = build_bundle_command(branch, out_path, repo_dir)
    if dry_run:
        print(" ".join(command))
        return 0
    return runner(command)


def apply(
    bundle_path: str,
    branch: str,
    *,
    repo_dir: str | None = None,
    dry_run: bool = False,
    runner: Runner = _subprocess_runner,
) -> int:
    """Fetch ``branch`` from a bundle into the host repo, hooks neutralised.

    Parameters
    ----------
    bundle_path : str
        The bundle file to apply.
    branch : str
        The ref to fetch.
    repo_dir : str or None, keyword-only, optional
        The host repository to fetch into.
    dry_run : bool, keyword-only, optional
        When True, print the command instead of running it.
    runner : callable, keyword-only, optional
        Executes the command and returns an exit code. Injectable for testing.

    Returns
    -------
    int
        The exit code (0 for a dry run).
    """
    command = build_apply_command(bundle_path, branch, repo_dir)
    if dry_run:
        print(" ".join(command))
        return 0
    return runner(command)
