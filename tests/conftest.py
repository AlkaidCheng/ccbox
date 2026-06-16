"""Shared pytest fixtures."""

import pytest

from ccbox.log import LOGGER_NAME, configure_logging, logger


@pytest.fixture(autouse=True)
def _ccbox_logging():
    """Bind the ccbox logger to the test's captured stderr for each test.

    ``main`` configures logging in production, but tests that call library
    functions directly bypass it. Binding here (under pytest's capture) lets
    ``capsys`` observe log output; the handler is removed afterwards so streams
    do not leak between tests.
    """
    configure_logging()
    yield
    for handler in [h for h in logger.handlers if getattr(h, "_ccbox", False)]:
        logger.removeHandler(handler)
    assert logger.name == LOGGER_NAME  # guard against accidental rename
