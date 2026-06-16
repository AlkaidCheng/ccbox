"""OCI-style backends sharing the Docker CLI surface: docker, podman, podman-hpc."""

from typing import Any

from ccbox.runtime.base import Runtime


def mount_to_volume(mount: dict[str, Any]) -> str:
    """Render one mount spec as a Docker ``src:dst:mode`` volume argument.

    Parameters
    ----------
    mount : dict
        Mapping with ``src`` (required), optional ``dst`` (defaults to ``src``),
        and ``mode`` (``"ro"`` or ``"rw"``, defaults to ``"ro"``).

    Returns
    -------
    str
        The ``src:dst:mode`` volume string.

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


KEEPALIVE_COMMAND: tuple[str, ...] = ("sleep", "infinity")


class OciRuntime(Runtime):
    """Docker-compatible CLI shared by docker, podman and podman-hpc."""

    supports_warm = True

    def _common_args(self, config: dict[str, Any]) -> list[str]:
        """Build the shared volume/env/workdir/network arguments."""
        args: list[str] = []
        for mount in config.get("mounts") or []:
            args += ["--volume", mount_to_volume(mount)]
        for variable in config.get("env") or []:
            args += ["--env", variable]
        workdir = config.get("workdir")
        if workdir:
            args += ["--workdir", workdir]
        if config.get("network") == "deny":
            args += ["--network", "none"]
        return args

    def build_run_command(self, config: dict[str, Any], argv: list[str]) -> list[str]:
        command = [self.binary, "run", "--rm", "-it", *self._common_args(config)]
        image = config.get("image")
        if image:
            command.append(image)
        command += list(argv)
        return command

    def build_create_command(self, config: dict[str, Any], name: str) -> list[str]:
        command = [self.binary, "run", "-d", "--name", name, *self._common_args(config)]
        image = config.get("image")
        if image:
            command.append(image)
        command += list(KEEPALIVE_COMMAND)
        return command

    def build_start_command(self, name: str) -> list[str]:
        return [self.binary, "start", name]

    def build_exec_command(self, name: str, argv: list[str]) -> list[str]:
        return [self.binary, "exec", "-it", name, *argv]


class DockerRuntime(OciRuntime):
    name = "docker"
    binary = "docker"


class PodmanRuntime(OciRuntime):
    name = "podman"
    binary = "podman"


class PodmanHpcRuntime(OciRuntime):
    name = "podman-hpc"
    binary = "podman-hpc"
