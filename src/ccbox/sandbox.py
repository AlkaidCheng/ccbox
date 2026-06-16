"""Launch the sandbox: inject Claude settings, build the command, and run it.

The project directory is mounted read-write and becomes the working directory,
the rendered ``.claude/settings.json`` is merged into the project so Claude
inside the sandbox picks up the deny rules, and the resolved runtime command runs
(or printed, with ``dry_run``). Mount paths support ``~`` and ``$VAR``
expansion so configs can reference e.g. ``$CONDA_PREFIX``.
"""

import copy
import json
import os
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ccbox.claude_settings import render_settings
from ccbox.runtime import get_runtime, resolve_runtime

CLAUDE_SETTINGS_RELPATH = Path(".claude") / "settings.json"
DEFAULT_INNER_COMMAND: tuple[str, ...] = ("claude",)

Runner = Callable[[list[str]], int]


def _expand_path(value: str) -> str:
    """Expand ``~`` and ``$VAR`` references in a filesystem path."""
    return os.path.expanduser(os.path.expandvars(value))


def expand_mounts(mounts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return mounts with ``~`` and environment variables expanded in paths.

    Only ``src`` and ``dst`` are expanded -- they must resolve on the host to
    bind-mount -- while modes and other keys are left untouched.

    Parameters
    ----------
    mounts : list of dict
        Mount specifications.

    Returns
    -------
    list of dict
        New mount dicts with expanded ``src``/``dst``.
    """
    expanded: list[dict[str, Any]] = []
    for mount in mounts:
        new_mount = dict(mount)
        if new_mount.get("src") is not None:
            new_mount["src"] = _expand_path(str(new_mount["src"]))
        if new_mount.get("dst"):
            new_mount["dst"] = _expand_path(str(new_mount["dst"]))
        expanded.append(new_mount)
    return expanded


def effective_config(config: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    """Return a copy of ``config`` with the project directory mounted.

    The project directory is bind-mounted read-write at its own absolute path
    and set as the working directory, so the agent operates on the real repo.
    Mount paths from the config are expanded (see :func:`expand_mounts`).

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
    mounts = expand_mounts(result.get("mounts") or [])
    if not any(str(mount.get("src")) == project_path for mount in mounts):
        mounts = [{"src": project_path, "dst": project_path, "mode": "rw"}, *mounts]
    result["mounts"] = mounts
    result["workdir"] = project_path
    return result


def _dedup(items: list[str]) -> list[str]:
    """Return ``items`` without duplicates, preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def merge_claude_settings(
    existing: dict[str, Any], rendered: dict[str, Any]
) -> dict[str, Any]:
    """Merge rendered permission rules into existing settings.

    Other top-level keys and permission entries in ``existing`` are preserved;
    ``permissions.deny`` and ``permissions.allow`` become the de-duplicated
    union of the existing and rendered lists (existing first). The merge is
    idempotent, so repeated runs do not accumulate duplicates.

    Parameters
    ----------
    existing : dict
        The settings already present on disk.
    rendered : dict
        The settings produced by :func:`ccbox.claude_settings.render_settings`.

    Returns
    -------
    dict
        The merged settings.
    """
    result = copy.deepcopy(existing)
    permissions = result.setdefault("permissions", {})
    rendered_permissions = rendered.get("permissions", {})
    for key in ("deny", "allow"):
        permissions[key] = _dedup(
            list(permissions.get(key, [])) + list(rendered_permissions.get(key, []))
        )
    return result


def write_claude_settings(config: dict[str, Any], project_dir: Path) -> Path:
    """Write the ``.claude/settings.json`` for the sandbox.

    When the file already exists, ccbox's deny/allow rules are merged into it
    (see :func:`merge_claude_settings`) rather than overwriting, preserving any
    other settings the project already has.

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

    Raises
    ------
    ValueError
        If an existing settings file is not a valid JSON object.
    """
    settings_path = Path(project_dir) / CLAUDE_SETTINGS_RELPATH
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_settings(config)
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"{settings_path}: existing settings is not valid JSON"
            ) from exc
        if not isinstance(existing, dict):
            raise ValueError(
                f"{settings_path}: existing settings must be a JSON object"
            )
        payload = merge_claude_settings(existing, rendered)
    else:
        payload = rendered
    settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
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
