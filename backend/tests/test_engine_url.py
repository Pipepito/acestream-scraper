"""engine_base_url: every module reads the configured engine address the same way."""
import pytest

from app.utils.engine_url import engine_base_url


@pytest.mark.parametrize('raw,expected', [
    ('engine.example:6878', 'http://engine.example:6878'),
    ('  engine.example:6878/  ', 'http://engine.example:6878'),
    ('http://engine.example:6878/', 'http://engine.example:6878'),
    ('https://engine.example', 'https://engine.example'),
    ('', ''),
    ('   ', ''),
    (None, ''),
])
def test_engine_base_url(raw, expected):
    assert engine_base_url(raw) == expected
