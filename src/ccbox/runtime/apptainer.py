"""Apptainer / Singularity backend (``exec`` with ``--bind``)."""

from typing import Any

from ccbox.runtime.base import Runtime


def mount_to_bind(mount: dict[str, Any]) -> str:
    """Render one mount spec as an Apptainer ``src:dst:mode`` bind argument.

    Parameters
    ----------
    mount : dict
        Mapping with ``src`` (required), optional ``dst`` (defaults to ``src``),
        and ``mode`` (``"ro"`` or ``"rw"``, defaults to ``"ro"``).

    Returns
    -------
    str
        The ``src:dst:mode`` bind string.

    Raises
    ------
    ValueError
        If ``mode`` is not ``"ro"`` or ``"rw"``.
    """
    source = mount["src"]
    destination = mount.get("dst") or source
    mode = mount.get("mode", "ro")
    if mode not in ("ro", "rw"):
        raise ValueError(f"mount mode must be 'ro' or 'rw', got {mode!r}")
    return f"{source}:{destination}:{mode}"


class ApptainerRuntime(Runtime):
    """Apptainer/Singularity backend; ``--containall`` isolates by default."""

    name = "apptainer"
    binary = "apptainer"

    def build_run_command(self, config: dict[str, Any], argv: list[str]) -> list[str]:
        command = [self.binary, "exec", "--containall"]
        for mount in config.get("mounts") or []:
            command += ["--bind", mount_to_bind(mount)]
        for variable in config.get("env") or []:
            command += ["--env", variable]
        workdir = config.get("workdir")
        if workdir:
            command += ["--pwd", workdir]
        if config.get("network") == "deny":
            command += ["--net", "--network", "none"]
        image = config.get("image")
        if not image:
            raise ValueError(
                "apptainer/singularity needs an 'image' (a .sif or docker:// URI)"
            )
        command.append(image)
        command += list(argv)
        return command


class SingularityRuntime(ApptainerRuntime):
    name = "singularity"
    binary = "singularity"
