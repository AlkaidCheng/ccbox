"""Classify image references and check runtime compatibility.

An image reference can be an OCI tag, a registry/remote URL, or an Apptainer
``.sif`` file. Runtimes accept different kinds: OCI runtimes take tags and pull
URLs, Apptainer/Singularity take ``.sif`` (and can build one from a URL or a
local OCI image), Shifter pulls registry images, and bwrap has no image
concept. This module is pure -- it classifies and validates; building, pulling,
and caching live elsewhere.
"""

from collections.abc import Sequence
from typing import Literal

ImageKind = Literal["oci-tag", "sif", "url"]
Compatibility = Literal["direct", "convert", "incompatible"]

_URL_SCHEMES = (
    "docker://",
    "docker-daemon://",
    "oras://",
    "library://",
    "shub://",
    "http://",
    "https://",
)

# Kinds each runtime can use without conversion.
_DIRECT: dict[str, set[ImageKind]] = {
    "docker": {"oci-tag", "url"},
    "podman": {"oci-tag", "url"},
    "podman-hpc": {"oci-tag", "url"},
    "apptainer": {"sif", "url"},
    "singularity": {"sif", "url"},
    "shifter": {"oci-tag", "url"},
    "bwrap": set(),
}

# Kinds a runtime can obtain by conversion (e.g. Apptainer builds a ``.sif``
# from a local OCI image).
_CONVERTIBLE: dict[str, set[ImageKind]] = {
    "apptainer": {"oci-tag"},
    "singularity": {"oci-tag"},
}


def image_kind(ref: str) -> ImageKind:
    """Classify an image reference.

    Parameters
    ----------
    ref : str
        The image reference (tag, URL, or path).

    Returns
    -------
    ImageKind
        ``"url"`` for a scheme-qualified remote ref, ``"sif"`` for a path
        ending in ``.sif``, otherwise ``"oci-tag"``.
    """
    lowered = ref.lower()
    if lowered.startswith(_URL_SCHEMES):
        return "url"
    if lowered.endswith(".sif"):
        return "sif"
    return "oci-tag"


def validate(ref: str, runtime: str) -> Compatibility:
    """Return how ``ref`` can be used by ``runtime``.

    Parameters
    ----------
    ref : str
        The image reference.
    runtime : str
        The runtime name.

    Returns
    -------
    Compatibility
        ``"direct"`` if usable as-is, ``"convert"`` if obtainable via
        conversion, ``"incompatible"`` otherwise.
    """
    kind = image_kind(ref)
    if kind in _DIRECT.get(runtime, set()):
        return "direct"
    if kind in _CONVERTIBLE.get(runtime, set()):
        return "convert"
    return "incompatible"


def pick_runtime(ref: str, candidates: Sequence[str]) -> str | None:
    """Return the first candidate runtime that can use ``ref``.

    Parameters
    ----------
    ref : str
        The image reference.
    candidates : sequence of str
        Runtime names in preference order.

    Returns
    -------
    str or None
        The first candidate whose :func:`validate` is not ``"incompatible"``,
        or ``None`` if no candidate can use it.
    """
    for runtime in candidates:
        if validate(ref, runtime) != "incompatible":
            return runtime
    return None
