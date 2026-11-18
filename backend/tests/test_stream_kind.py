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


from app.utils.stream_kind import is_acestream_id, is_http_id


@pytest.mark.parametrize('value,acestream,http', [
    ('a' * 40, True, False),
    ('A' * 40, True, False),
    ('url:' + 'a' * 40, False, True),
    ('url:' + 'A' * 40, False, False),
    ('a' * 39, False, False),
    ('a' * 40 + '\n', False, False),
    ('g' * 40, False, False),
    (None, False, False),
])
def test_stream_id_shapes(value, acestream, http):
    assert is_acestream_id(value) is acestream
    assert is_http_id(value) is http
