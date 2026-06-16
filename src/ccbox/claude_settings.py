"""Render the in-sandbox ``.claude/settings.json`` from ccbox config.

The deny rules form the inner enforcement layer: they gate Claude's own file
tools (and recognised Bash file commands such as ``cat`` and ``sed``) but not
arbitrary subprocesses, which is how project code can still reach a path that
Claude itself is denied.
"""

from typing import Any


def render_settings(config: dict[str, Any]) -> dict[str, Any]:
    """Build the ``.claude/settings.json`` mapping written into the sandbox.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.

    Returns
    -------
    dict
        A settings mapping with ``permissions.deny`` and ``permissions.allow``
        populated from ``config["claude"]``.
    """
    claude = config.get("claude") or {}
    return {
        "permissions": {
            "deny": list(claude.get("deny", [])),
            "allow": list(claude.get("allow", [])),
        }
    }
