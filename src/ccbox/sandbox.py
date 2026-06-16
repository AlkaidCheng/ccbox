"""Launch the sandbox: inject Claude settings, build the command, and run it.

The project directory is mounted read-write and becomes the working directory,
the rendered ``.claude/settings.json`` is written into it so Claude inside the
sandbox picks up the deny rules, and the resolved runtime command is executed
(or printed, with ``dry_run``).
"""

import copy
import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from .claude_settings import render_settings
from .runtime import get_runtime, resolve_runtime

CLAUDE_SETTINGS_RELPATH = Path(".claude") / "settings.json"
DEFAULT_INNER_COMMAND: tuple[str, ...] = ("claude",)

Runner = Callable[[list[str]], int]


def effective_config(config: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    """Return a copy of ``config`` with the project directory mounted.

    The project directory is bind-mounted read-write at its own absolute path
    and set as the working directory, so the agent operates on the real repo.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.
    project_dir : Path
        The project directory to expose in the sandbox.

    Returns
    -------
    dict
        A deep copy of ``config`` with the project mount prepended and
        ``workdir`` pointed at the project directory.
    """
    project_path = str(Path(project_dir).resolve())
    result = copy.deepcopy(config)
    mounts = result.get("mounts") or []
    if not any(str(mount.get("src")) == project_path for mount in mounts):
        mounts = [{"src": project_path, "dst": project_path, "mode": "rw"}, *mounts]
    result["mounts"] = mounts
    result["workdir"] = project_path
    return result


def write_claude_settings(config: dict[str, Any], project_dir: Path) -> Path:
    """Write the rendered ``.claude/settings.json`` into the project directory.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.
    project_dir : Path
        The project directory to write settings into.

    Returns
    -------
    Path
        The path to the written settings file.
    """
    settings_path = Path(project_dir) / CLAUDE_SETTINGS_RELPATH
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(render_settings(config), indent=2) + "\n", encoding="utf-8"
    )
    return settings_path


def build_enter_command(
    config: dict[str, Any], argv: Sequence[str] | None = None
) -> tuple[str, list[str]]:
    """Resolve the runtime and build the full sandbox invocation.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration (project mount already applied).
    argv : sequence of str or None, optional
        Command to run inside the sandbox. Defaults to launching ``claude``.

    Returns
    -------
    tuple[str, list[str]]
        The resolved runtime name and the argument vector to execute.

    Raises
    ------
    ValueError
        If the runtime needs an image and none is configured.
    """
    name = resolve_runtime(config)
    runtime = get_runtime(name)
    if runtime.requires_image and not config.get("image"):
        raise ValueError(
            f"runtime {name!r} requires an 'image'; set one in .ccbox.yaml"
        )
    inner = list(argv) if argv else list(DEFAULT_INNER_COMMAND)
    return name, runtime.build_run_command(config, inner)


def _subprocess_runner(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def enter(
    config: dict[str, Any],
    project_dir: Path,
    argv: Sequence[str] | None = None,
    *,
    dry_run: bool = False,
    runner: Runner = _subprocess_runner,
) -> int:
    """Prepare and launch the sandbox for ``project_dir``.

    Applies the project mount, builds the command, and—unless ``dry_run``—
    writes ``.claude/settings.json`` and runs the command.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.
    project_dir : Path
        The project directory to sandbox.
    argv : sequence of str or None, optional
        Command to run inside the sandbox. Defaults to ``claude``.
    dry_run : bool, keyword-only, optional
        When True, print the command without writing settings or running.
    runner : callable, keyword-only, optional
        Executes the command and returns an exit code. Injectable for testing.

    Returns
    -------
    int
        The exit code of the sandbox command (0 for a dry run).
    """
    prepared = effective_config(config, Path(project_dir))
    name, command = build_enter_command(prepared, argv)
    if dry_run:
        print(f"# runtime: {name}")
        print(" ".join(command))
        return 0
    write_claude_settings(prepared, Path(project_dir))
    return runner(command)
