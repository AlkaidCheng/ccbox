"""Pull an image from a remote URL.

OCI runtimes pull into their local image store (the daemon/store caches it);
Apptainer and Singularity pull a ``.sif`` file, which ccbox caches under its
cache directory. This module is pure -- it computes the pull command and the
cache filename; running it and locating the cache live in the CLI layer.
"""

import hashlib
import re

# Runtimes that pull into a local OCI image store.
OCI_PULL_RUNTIMES = ("docker", "podman", "podman-hpc")
# Runtimes that pull a standalone ``.sif`` artifact.
SIF_PULL_RUNTIMES = ("apptainer", "singularity")

_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*://")


def strip_scheme(ref: str) -> str:
    """Return ``ref`` without a leading ``scheme://`` prefix.

    OCI ``pull`` wants a bare ``registry/name:tag`` rather than a transport URI,
    so a ``docker://`` (or similar) prefix is removed.
    """
    return _SCHEME_RE.sub("", ref, count=1)


def sif_filename(ref: str) -> str:
    """Return a stable, collision-resistant ``.sif`` filename for ``ref``.

    The last path component seeds a readable name and a short hash of the full
    reference disambiguates images that share a name across registries.
    """
    base = strip_scheme(ref).rstrip("/").split("/")[-1]
    base = base.replace(":", "_").replace("@", "_") or "image"
    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}.sif"


def pull_image_command(
    runtime: str, binary: str, ref: str, sif_path: str | None = None
) -> list[str]:
    """Return the command that pulls ``ref`` for ``runtime``.

    Parameters
    ----------
    runtime : str
        The resolved runtime name.
    binary : str
        The runtime's executable.
    ref : str
        The image URL to pull.
    sif_path : str or None, optional
        Destination ``.sif`` path, required for ``.sif``-pulling runtimes.

    Returns
    -------
    list[str]
        The ``pull`` argument vector.

    Raises
    ------
    ValueError
        If ``runtime`` cannot pull a URL, or a ``.sif`` runtime is given no
        ``sif_path``.
    """
    if runtime in OCI_PULL_RUNTIMES:
        return [binary, "pull", strip_scheme(ref)]
    if runtime in SIF_PULL_RUNTIMES:
        if not sif_path:
            raise ValueError(f"{runtime} pull needs a destination .sif path")
        return [binary, "pull", sif_path, ref]
    raise ValueError(f"runtime {runtime!r} cannot pull image URLs")
