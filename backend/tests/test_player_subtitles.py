import pytest
from app.services.player_subtitles import media_clock_webvtt


def test_maps_segment_local_cues_and_preserves_settings_and_text():
    text = ('WEBVTT\r\nX-TIMESTAMP-MAP=LOCAL:00:00:10.000,MPEGTS:9000000\r\n\r\n'
            'cue-id\r\n00:00:10.500 --> 00:00:12.000 align:start\r\nCaption\r\n')
    out = media_clock_webvtt(text)
    assert '00:01:40.500 --> 00:01:42.000 align:start' in out
    assert 'cue-id\n' in out and '\nCaption\n' in out
    assert 'X-TIMESTAMP-MAP' not in out
    # Consecutive segments use their own mapping, not a reused first offset.
    assert '00:01:44.500' in media_clock_webvtt(text.replace('9000000', '9360000'))


def test_unmapped_and_empty_segments():
    plain = 'WEBVTT\n\n00:03.000 --> 00:05.000\nCaption\n'
    assert media_clock_webvtt(plain) == plain
    assert media_clock_webvtt('WEBVTT\nX-TIMESTAMP-MAP=MPEGTS:90000,LOCAL:00:00:00.000\n\n') == 'WEBVTT\n\n\n'


@pytest.mark.parametrize('mapping', [
    'MPEGTS:8589934592,LOCAL:00:00:00.000', 'MPEGTS:-1,LOCAL:00:00:00.000',
    'MPEGTS:90000,LOCAL:00:99:00.000', 'MPEGTS:90000', 'bad',
])
def test_invalid_maps_fail_closed(mapping):
    with pytest.raises(ValueError):
        media_clock_webvtt('WEBVTT\nX-TIMESTAMP-MAP=' + mapping + '\n\n')
