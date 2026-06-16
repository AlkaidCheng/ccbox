"""Configuration loading and layered merge for ccbox.

Configuration is layered, mirroring Claude Code's own user -> project model:

    global  : <platform config dir>/ccbox/config.yaml   (defaults, safety rules)
    project : <repo>/.ccbox.yaml                         (per-project settings)

The project layer is merged over the global layer: dicts merge recursively,
lists concatenate (global first), and scalars are overridden by the project.
"""

import copy
import os
import sys
from pathlib import Path
from typing import Any, TypeAlias

import yaml

PROJECT_CONFIG_FILENAME = ".ccbox.yaml"

Config: TypeAlias = dict[str, Any]

# Safety deny rules always applied to Claude's file tools, regardless of mode.
# These guard against accidental access; the mount set is the hard boundary.
DEFAULT_CLAUDE_DENY = [
    "Read(~/.ssh/**)",
    "Read(~/.aws/**)",
    "Read(~/.config/gcloud/**)",
    "Read(**/.env)",
    "Read(**/*token*)",
    "Read(**/*secret*)",
]

DEFAULT_CONFIG: Config = {
    "mode": "accident",  # "accident" | "adversarial"
    "runtime": "auto",  # "auto" detects; or name a backend explicitly
    "image": None,
    "workdir": ".",
    "network": "allow",  # "allow" | "deny" | [list of allowed hosts]
    "mounts": [],  # [{src, dst?, mode: ro|rw, same_path?: bool}]
    "env": [],  # ["NAME=VALUE", ...]
    "claude": {
        "deny": list(DEFAULT_CLAUDE_DENY),
        "allow": [],
    },
}


def default_global_config_path() -> Path:
    """Return the global config file path for the current platform.

    Honors ``XDG_CONFIG_HOME`` when set; otherwise uses ``%APPDATA%`` on
    Windows and ``~/.config`` elsewhere.

    Returns
    -------
    Path
        Location of ``config.yaml`` under the ccbox config directory.
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        base = Path(xdg_config_home)
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path.home() / ".config"
    return base / "ccbox" / "config.yaml"


def deep_merge(base: Any, override: Any) -> Any:
    """Merge ``override`` onto ``base`` and return the result.

    Parameters
    ----------
    base : Any
        The lower-precedence value.
    override : Any
        The higher-precedence value layered on top of ``base``.

    Returns
    -------
    Any
        ``dict`` values are merged recursively, ``list`` values are
        concatenated (``base`` first), and any other type is replaced by
        ``override``.
    """
    if isinstance(base, dict) and isinstance(override, dict):
        merged = {key: copy.deepcopy(value) for key, value in base.items()}
        for key, value in override.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        return merged
    if isinstance(base, list) and isinstance(override, list):
        return [copy.deepcopy(item) for item in base + override]
    return copy.deepcopy(override)


def _load_yaml(path: Path) -> Config:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level config must be a mapping")
    return data


def load_config(
    project_dir: str | os.PathLike[str] | None = None,
    global_path: str | os.PathLike[str] | None = None,
) -> Config:
    """Load and merge the effective configuration.

    Parameters
    ----------
    project_dir : path-like or None, optional
        Project directory holding ``.ccbox.yaml``. Defaults to the current
        working directory.
    global_path : path-like or None, optional
        Path to the global config file. Defaults to
        :func:`default_global_config_path`.

    Returns
    -------
    Config
        The merged configuration: defaults, then global, then project.
    """
    project = Path(project_dir) if project_dir is not None else Path.cwd()
    if global_path is not None:
        global_file = Path(global_path)
    else:
        global_file = default_global_config_path()
    config = deep_merge(DEFAULT_CONFIG, _load_yaml(global_file))
    return deep_merge(config, _load_yaml(project / PROJECT_CONFIG_FILENAME))
