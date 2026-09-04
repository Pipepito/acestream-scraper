import logging

from app.utils.logging import RedactTokenFilter, setup_logging


def _record(args):
    return logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d', args, None)


def test_filter_redacts_token_in_args():
    record = _record(("127.0.0.1:1", "GET", "/api/v1/player/sessions/x/index.m3u8?token=T0p&x=1", "1.1", 200))
    assert RedactTokenFilter().filter(record) is True
    assert record.args[2] == "/api/v1/player/sessions/x/index.m3u8?token=[redacted]&x=1"
    assert "T0p" not in record.getMessage()


def test_filter_leaves_other_paths_alone():
    record = _record(("127.0.0.1:1", "GET", "/api/v1/health", "1.1", 200))
    RedactTokenFilter().filter(record)
    assert record.args[2] == "/api/v1/health"


def test_setup_logging_installs_the_filter_once():
    setup_logging()
    setup_logging()
    filters = [f for f in logging.getLogger("uvicorn.access").filters if isinstance(f, RedactTokenFilter)]
    assert len(filters) == 1
