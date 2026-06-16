"""bubblewrap backend. Placeholder registered for detection only."""

from typing import Any

from .base import Runtime


class BwrapRuntime(Runtime):
    """bubblewrap backend; command building is planned for a later phase."""

    name = "bwrap"
    binary = "bwrap"
    implemented = False

    def build_run_command(self, config: dict[str, Any], argv: list[str]) -> list[str]:
        raise NotImplementedError("the bwrap backend is planned for a later phase")
