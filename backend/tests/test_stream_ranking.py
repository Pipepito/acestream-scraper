from types import SimpleNamespace

from app.services.stream_ranking import score_acestream, sort_streams_curated


def _s(id, **kw):
    base = dict(is_online=None, logo=None, tvg_id=None, tvg_name=None)
    base.update(kw)
    return SimpleNamespace(id=id, **base)


def test_weights_match_the_playlist_contract():
    assert score_acestream(_s("a")) == 0
    assert score_acestream(_s("a", is_online=True)) == 10
    assert score_acestream(_s("a", logo="l")) == 3
    assert score_acestream(_s("a", tvg_id="t")) == 2
    assert score_acestream(_s("a", tvg_name="n")) == 1
    assert score_acestream(_s("a", is_online=True, logo="l", tvg_id="t", tvg_name="n")) == 16


def test_sort_is_score_desc_then_id():
    streams = [_s("c", logo="l"), _s("b", is_online=True), _s("a", is_online=True)]
    assert [s.id for s in sort_streams_curated(streams)] == ["a", "b", "c"]


def test_stream_order_takes_precedence():
    streams = [
        _s("c", stream_order=2, is_online=True),
        _s("b", stream_order=1, is_online=False),
        _s("a", stream_order=3, is_online=True, logo="l"),
    ]
    assert [s.id for s in sort_streams_curated(streams)] == ["b", "c", "a"]


def test_mixed_stream_order_and_score():
    streams = [
        _s("unordered_offline", stream_order=None, is_online=False),
        _s("ordered_second", stream_order=2, is_online=False),
        _s("unordered_online", stream_order=None, is_online=True),
        _s("ordered_first", stream_order=1, is_online=False),
    ]
    assert [s.id for s in sort_streams_curated(streams)] == [
        "ordered_first",
        "ordered_second",
        "unordered_online",
        "unordered_offline",
    ]
