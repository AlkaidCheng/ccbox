"""Launch the sandbox: inject Claude settings, build the command, and run it.

The project directory is mounted read-write and becomes the working directory,
the rendered ``.claude/settings.json`` is merged into the project so Claude
inside the sandbox picks up the deny rules, and the resolved runtime command runs
(or printed, with ``dry_run``). Mount paths support ``~`` and ``$VAR``
expansion so configs can reference e.g. ``$CONDA_PREFIX``.
"""

import copy
import hashlib
import json
import os
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ccbox.claude_settings import render_settings
from ccbox.runtime import Runtime, get_runtime, resolve_runtime

CLAUDE_SETTINGS_RELPATH = Path(".claude") / "settings.json"
DEFAULT_INNER_COMMAND: tuple[str, ...] = ("claude",)

Runner = Callable[[list[str]], int]
StatusChecker = Callable[[str, str], str]


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


def container_name(project_dir: Path) -> str:
    """Return a stable container name derived from the project directory.

    Parameters
    ----------
    project_dir : Path
        The project directory.

    Returns
    -------
    str
        A name of the form ``ccbox-<10 hex digits>``, stable across runs for
        the same resolved path.
    """
    digest = hashlib.sha1(str(Path(project_dir).resolve()).encode()).hexdigest()[:10]
    return f"ccbox-{digest}"


def _container_status(binary: str, name: str) -> str:
    try:
        result = subprocess.run(
            [binary, "container", "inspect", "--format", "{{.State.Running}}", name],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "absent"
    if result.returncode != 0:
        return "absent"
    return "running" if result.stdout.strip() == "true" else "stopped"


def warm_command_sequence(
    runtime: Runtime,
    config: dict[str, Any],
    name: str,
    argv: list[str],
    status: StatusChecker,
) -> list[list[str]]:
    """Return the command(s) to warm-enter, based on the container's status.

    Parameters
    ----------
    runtime : Runtime
        A warm-capable backend.
    config : dict
        The effective ccbox configuration.
    name : str
        The container name.
    argv : list[str]
        The command to run inside the container.
    status : callable
        Maps ``(binary, name)`` to ``"running"``, ``"stopped"`` or ``"absent"``.

    Returns
    -------
    list[list[str]]
        ``running`` -> exec; ``stopped`` -> start then exec; ``absent`` ->
        create then exec.
    """
    state = status(runtime.binary, name)
    exec_command = runtime.build_exec_command(name, argv)
    if state == "running":
        return [exec_command]
    if state == "stopped":
        return [runtime.build_start_command(name), exec_command]
    return [runtime.build_create_command(config, name), exec_command]


def enter(
    config: dict[str, Any],
    project_dir: Path,
    argv: Sequence[str] | None = None,
    *,
    dry_run: bool = False,
    runner: Runner = _subprocess_runner,
    warm: bool = False,
    status: StatusChecker = _container_status,
) -> int:
    """Prepare and launch the sandbox for ``project_dir``.

    Applies the project mount and writes ``.claude/settings.json``, then runs
    the resolved runtime command. With ``warm``, a persistent per-project
    container is created on first use and re-entered with ``exec`` thereafter.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.
    project_dir : Path
        The project directory to sandbox.
    argv : sequence of str or None, optional
        Command to run inside the sandbox. Defaults to ``claude``.
    dry_run : bool, keyword-only, optional
        When True, print the command(s) without writing settings or running.
    runner : callable, keyword-only, optional
        Executes a command and returns an exit code. Injectable for testing.
    warm : bool, keyword-only, optional
        Reuse a persistent named container (OCI backends only).
    status : callable, keyword-only, optional
        Maps ``(binary, name)`` to container state. Injectable for testing.

    Returns
    -------
    int
        The exit code of the last sandbox command (0 for a dry run).

    Raises
    ------
    ValueError
        If ``warm`` is set for a backend that does not support it, or the
        runtime needs an image and none is configured.
    """
    prepared = effective_config(config, Path(project_dir))
    inner = list(argv) if argv else list(DEFAULT_INNER_COMMAND)
    if warm:
        runtime_name = resolve_runtime(prepared)
        runtime = get_runtime(runtime_name)
        if not runtime.supports_warm:
            raise ValueError(
                f"runtime {runtime_name!r} does not support warm container reuse"
            )
        if runtime.requires_image and not prepared.get("image"):
            raise ValueError(
                f"runtime {runtime_name!r} requires an 'image'; set one in .ccbox.yaml"
            )
        commands = warm_command_sequence(
            runtime, prepared, container_name(project_dir), inner, status
        )
    else:
        runtime_name, command = build_enter_command(prepared, argv)
        commands = [command]
    if dry_run:
        print(f"# runtime: {runtime_name}")
        for command in commands:
            print(" ".join(command))
        return 0
    write_claude_settings(prepared, Path(project_dir))
    exit_code = 0
    for command in commands:
        exit_code = runner(command)
        if exit_code:
            break
    return exit_code
