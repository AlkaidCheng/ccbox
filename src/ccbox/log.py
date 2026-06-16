"""Logging for the ccbox CLI.

Diagnostics, status notices, and errors go through the shared ``ccbox`` logger,
which writes to stderr. Genuine result data -- ``config``/``render`` JSON, the
``--dry-run`` command lines, and the ``doctor``/``runtimes`` reports -- is
written to stdout with ``print`` so it stays pipeable.
"""

from __future__ import annotations

import logging
import sys

LOGGER_NAME = "ccbox"

logger = logging.getLogger(LOGGER_NAME)


class _Formatter(logging.Formatter):
    """Render records as ``[ccbox] <level>: <message>`` with a lowercased level."""

    def format(self, record: logging.LogRecord) -> str:
        return f"[{LOGGER_NAME}] {record.levelname.lower()}: {record.getMessage()}"


class _StderrHandler(logging.StreamHandler):
    """A stream handler that resolves ``sys.stderr`` lazily at emit time.

    Binding to the live stream (rather than the one present at construction)
    lets stderr redirection and test capture (pytest's ``capsys``) take effect,
    mirroring the standard library's last-resort handler.
    """

    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stderr
        super().emit(record)


def configure_logging(level: int = logging.INFO) -> None:
    """Attach a stderr handler to the ``ccbox`` logger.

    Safe to call more than once: any handler this function added previously is
    replaced. Applications call this once at startup; library callers that
    bypass the CLI must call it to see log output.

    Parameters
    ----------
    level : int, optional
        Threshold below which records are dropped. Defaults to ``logging.INFO``.
    """
    logger.setLevel(level)
    for handler in [h for h in logger.handlers if getattr(h, "_ccbox", False)]:
        logger.removeHandler(handler)
    handler = _StderrHandler()
    handler.setFormatter(_Formatter())
    handler._ccbox = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    logger.propagate = False
