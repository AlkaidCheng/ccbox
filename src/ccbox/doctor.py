"""Static safety checks on an effective config (the ``ccbox doctor`` command).

Checks are pure functions of the config mapping, so they are easy to unit test
and independent of the host platform. ``error`` issues block ``ccbox enter``;
``warn`` issues do not.
"""

from dataclasses import dataclass
from typing import Any

from .runtime import REGISTRY

# Substrings that flag a likely-sensitive mount source in any mode.
SENSITIVE_SRC_HINTS = (
    ".ssh",
    ".aws",
    ".gnupg",
    ".netrc",
    ".npmrc",
    "id_rsa",
    "id_ed25519",
)


@dataclass
class Issue:
    """A single problem found in a configuration.

    Attributes
    ----------
    level : str
        Either ``"error"`` (blocks ``enter``) or ``"warn"`` (advisory).
    message : str
        Human-readable description of the problem.
    """

    level: str
    message: str


def check(config: dict[str, Any]) -> list[Issue]:
    """Return the list of safety issues found in ``config``.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.

    Returns
    -------
    list[Issue]
        Issues in discovery order. Empty when no problems are found.
    """
    issues: list[Issue] = []
    mode = config.get("mode", "accident")
    mounts = config.get("mounts") or []
    network = config.get("network", "allow")
    runtime = config.get("runtime", "auto")

    if runtime != "auto" and runtime not in REGISTRY:
        issues.append(Issue("error", f"unknown runtime: {runtime!r}"))

    for mount in mounts:
        source = str(mount.get("src", ""))
        if any(hint in source for hint in SENSITIVE_SRC_HINTS):
            issues.append(Issue("error", f"sensitive path mounted: {source}"))

    if mode == "adversarial":
        if network != "deny" and not isinstance(network, list):
            issues.append(
                Issue(
                    "error", "adversarial mode requires network: deny or an allowlist"
                )
            )
        for mount in mounts:
            if (mount.get("mode") or "ro") == "rw":
                source = mount.get("src")
                message = f"rw mount is a write channel in adversarial mode: {source}"
                issues.append(Issue("warn", message))

    return issues
