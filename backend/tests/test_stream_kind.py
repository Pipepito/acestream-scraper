"""stream_kind: the one rule for which input a stored stream ID addresses."""
import pytest

from app.utils.stream_kind import stream_kind


@pytest.mark.parametrize('content_id,kind', [
    ('url:' + 'a' * 40, 'http'),
    ('url:', 'http'),
    ('a' * 40, 'acestream'),
    ('URL:' + 'a' * 40, 'acestream'),
    (' url:' + 'a' * 40, 'acestream'),
    ('', 'acestream'),
])
def test_only_the_exact_url_prefix_is_http(content_id, kind):
    assert stream_kind(content_id) == kind
