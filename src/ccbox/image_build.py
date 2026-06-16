"""Build an OCI image from a Dockerfile recipe.

Apptainer/Singularity and Shifter consume OCI images (convert/pull), so an OCI
image built from the user's Dockerfile is the universal artifact -- only an OCI
builder is needed to produce it. The built image is cached in the builder's
local image store under its tag.
"""

import shutil

OCI_BUILDERS = ("podman-hpc", "podman", "docker")


def detect_builder() -> str | None:
    """Return the first available OCI image builder on PATH, or ``None``."""
    for binary in OCI_BUILDERS:
        if shutil.which(binary) is not None:
            return binary
    return None


def build_image_command(
    binary: str, image: str, recipe: str, context: str
) -> list[str]:
    """Return the command that builds ``image`` from ``recipe``.

    Parameters
    ----------
    binary : str
        The OCI builder binary (e.g. ``docker``).
    image : str
        The image tag to build.
    recipe : str
        Path to the Dockerfile.
    context : str
        The build context directory.

    Returns
    -------
    list[str]
        The ``build`` argument vector.
    """
    return [binary, "build", "-t", image, "-f", recipe, context]
