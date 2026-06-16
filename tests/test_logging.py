import logging

from ccbox.log import LOGGER_NAME, configure_logging, logger


def test_configure_logging_writes_to_stderr(capsys):
    configure_logging()
    logger.error("boom")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "[ccbox] error: boom" in captured.err


def test_info_is_emitted_at_default_level(capsys):
    configure_logging()
    logger.info("hello")
    assert "[ccbox] info: hello" in capsys.readouterr().err


def test_configure_logging_is_idempotent():
    configure_logging()
    configure_logging()
    ccbox_handlers = [h for h in logger.handlers if getattr(h, "_ccbox", False)]
    assert len(ccbox_handlers) == 1


def test_level_threshold_drops_below(capsys):
    configure_logging(level=logging.ERROR)
    logger.info("quiet")
    logger.error("loud")
    captured = capsys.readouterr()
    assert "quiet" not in captured.err
    assert "loud" in captured.err
    configure_logging()  # restore default level for later tests


def test_logger_name():
    assert logger.name == LOGGER_NAME
