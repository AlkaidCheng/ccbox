"""Runtime backend registry and environment-based auto-detection.

ccbox is runtime-agnostic. ``runtime: auto`` (the default) probes ``PATH`` and
picks the first available implemented backend in :data:`DETECTION_ORDER`.
Override by naming a backend explicitly in config, e.g. ``runtime: docker``.
"""

import shutil
from typing import Any

from .apptainer import ApptainerRuntime, SingularityRuntime
from .base import Runtime
from .bwrap import BwrapRuntime
from .oci import DockerRuntime, PodmanHpcRuntime, PodmanRuntime
from .shifter import ShifterRuntime

# Order encodes preference (first available wins). HPC-native and rootless
# backends rank ahead of Docker; the two stubs rank last and are skipped by
# auto-detection until implemented.
_CLASSES: list[type[Runtime]] = [
    PodmanHpcRuntime,
    ShifterRuntime,
    ApptainerRuntime,
    SingularityRuntime,
    PodmanRuntime,
    DockerRuntime,
    BwrapRuntime,
]

REGISTRY: dict[str, type[Runtime]] = {cls.name: cls for cls in _CLASSES}
DETECTION_ORDER: list[str] = [cls.name for cls in _CLASSES]

__all__ = [
    "Runtime",
    "REGISTRY",
    "DETECTION_ORDER",
    "get_runtime",
    "detect_runtime",
    "resolve_runtime",
]


def get_runtime(name: str) -> Runtime:
    """Instantiate a backend by name.

    Parameters
    ----------
    name : str
        A backend identifier present in :data:`REGISTRY`.

    Returns
    -------
    Runtime
        A new backend instance.

    Raises
    ------
    ValueError
        If ``name`` is not a known backend.
    """
    try:
        return REGISTRY[name]()
    except KeyError:
        raise ValueError(f"unknown runtime: {name!r}") from None


def detect_runtime(
    order: list[str] | None = None,
    include_unimplemented: bool = False,
) -> str | None:
    """Return the first available backend in preference order.

    Parameters
    ----------
    order : list[str] or None, optional
        Backend names to probe, most preferred first. Defaults to
        :data:`DETECTION_ORDER`.
    include_unimplemented : bool, optional
        Whether to consider backends whose command builder is not implemented.
        Defaults to ``False``.

    Returns
    -------
    str or None
        The name of the first backend whose binary is on ``PATH``, or ``None``
        if none are available.
    """
    for name in order or DETECTION_ORDER:
        backend = REGISTRY.get(name)
        if backend is None:
            continue
        if not include_unimplemented and not backend.implemented:
            continue
        if shutil.which(backend.binary) is not None:
            return name
    return None


def resolve_runtime(config: dict[str, Any]) -> str:
    """Resolve the configured runtime, expanding ``auto`` via detection.

    Parameters
    ----------
    config : dict
        The effective ccbox configuration.

    Returns
    -------
    str
        A concrete backend name.

    Raises
    ------
    ValueError
        If an explicit runtime name is not recognised.
    RuntimeError
        If ``runtime`` is ``auto`` and no backend is available.
    """
    name = config.get("runtime", "auto")
    if name == "auto":
        detected = detect_runtime()
        if detected is None:
            raise RuntimeError(
                "no supported container runtime found on PATH "
                f"(looked for: {', '.join(REGISTRY)})"
            )
        return detected
    if name not in REGISTRY:
        raise ValueError(f"unknown runtime: {name!r}")
    return name
