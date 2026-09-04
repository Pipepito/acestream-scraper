import pytest
from app.services.stream_service import StreamService

service = StreamService()

@pytest.mark.parametrize("url,expected", [
    ("acestream://1234567890abcdef1234567890abcdef12345678", "1234567890abcdef1234567890abcdef12345678"),
    ("acestream://ABCDEF1234567890ABCDEF1234567890ABCDEF12", "ABCDEF1234567890ABCDEF1234567890ABCDEF12"),
    ("http://example.com/stream?id=1234567890abcdef1234567890abcdef12345678", "1234567890abcdef1234567890abcdef12345678"),
    ("https://foo.com/watch?pid=ABCDEF1234567890ABCDEF1234567890ABCDEF12", "ABCDEF1234567890ABCDEF1234567890ABCDEF12"),
    ("https://bar.com/stream/1234567890abcdef1234567890abcdef12345678", "1234567890abcdef1234567890abcdef12345678"),
    ("https://bar.com/stream/garbage/1234567890abcdef1234567890abcdef12345678/extra", "1234567890abcdef1234567890abcdef12345678"),
    ("https://baz.com/stream?stream_id=ABCDEF1234567890ABCDEF1234567890ABCDEF12", "ABCDEF1234567890ABCDEF1234567890ABCDEF12"),
    ("https://baz.com/stream?acestream_id=ABCDEF1234567890ABCDEF1234567890ABCDEF12", "ABCDEF1234567890ABCDEF1234567890ABCDEF12"),
    ("https://baz.com/stream?notanid=foo", None),
    ("https://baz.com/stream", None),
    ("", None),
    (None, None),
    (12345, None),
])
def test_extract_acestream_id(url, expected):
    assert service.extract_acestream_id(url) == expected
