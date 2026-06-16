"""Shifter backend (NERSC). Placeholder registered for detection only."""

from typing import Any

from .base import Runtime


class ShifterRuntime(Runtime):
    """Shifter backend; command building is not implemented yet."""

    name = "shifter"
    binary = "shifter"
    implemented = False

    def build_run_command(self, config: dict[str, Any], argv: list[str]) -> list[str]:
        raise NotImplementedError(
            "the shifter backend is not implemented yet; set 'runtime' explicitly"
        )
