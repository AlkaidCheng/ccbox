"""Abstract base class for container runtime backends."""

import abc
import shutil
from typing import Any


class Runtime(abc.ABC):
    """A container or sandbox backend.

    Subclasses set :attr:`name` (the ccbox identifier) and :attr:`binary` (the
    executable looked up on ``PATH``), and implement :meth:`build_run_command`.
    """

    name: str = "base"
    binary: str = ""
    implemented: bool = True

    @classmethod
    def available(cls) -> bool:
        """Return whether this runtime's binary is found on ``PATH``."""
        return bool(cls.binary) and shutil.which(cls.binary) is not None

    @abc.abstractmethod
    def build_run_command(self, config: dict[str, Any], argv: list[str]) -> list[str]:
        """Return the argv that launches ``argv`` inside the sandbox.

        Parameters
        ----------
        config : dict
            The effective ccbox configuration.
        argv : list[str]
            The command to run inside the sandbox.

        Returns
        -------
        list[str]
            The full runtime invocation as an argument vector.
        """
        raise NotImplementedError
