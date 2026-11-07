"""Translate HLS WebVTT's local clock before FFmpeg demuxes its cues.

FFmpeg 8's WebVTT demuxer ignores X-TIMESTAMP-MAP. Only the private input
proxy uses this translation; browsers receive FFmpeg's remuxed WebVTT output.
"""
from __future__ import annotations

import re

_TIMESTAMP = r'(?:\d{2,}:)?\d{2}:\d{2}\.\d{3}'
_CUE = re.compile(rf'^({_TIMESTAMP})([ \t]+-->[ \t]+)({_TIMESTAMP})([^\r\n]*)$', re.MULTILINE)
_MAP = re.compile(r'^X-TIMESTAMP-MAP=([^\r\n]+)', re.MULTILINE)


def _milliseconds(value: str) -> int:
    parts = value.split(':')
    seconds, millis = parts.pop().split('.')
    minutes = int(parts.pop())
    hours = int(parts.pop()) if parts else 0
    if minutes >= 60 or int(seconds) >= 60 or hours > 100000:
        raise ValueError('Invalid subtitle timestamp')
    return ((hours * 60 + minutes) * 60 + int(seconds)) * 1000 + int(millis)


def _timestamp(value: int) -> str:
    if value < 0:
        raise ValueError('Subtitle timestamp precedes the media clock')
    seconds, millis = divmod(value, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}'


def media_clock_webvtt(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    mapping = _MAP.search(text)
    if mapping is None:
        return text
    fields = dict(item.split(':', 1) for item in mapping[1].split(','))
    local = fields.get('LOCAL', '')
    if not re.fullmatch(_TIMESTAMP, local) or not re.fullmatch(r'\d{1,10}', fields.get('MPEGTS', '')):
        raise ValueError('Invalid subtitle timestamp map')
    ticks = int(fields['MPEGTS'])
    if ticks >= 1 << 33:
        raise ValueError('Invalid MPEG timestamp')
    offset = round(ticks / 90) - _milliseconds(local)
    def cue(match: re.Match) -> str:
        start, end = _milliseconds(match[1]) + offset, _milliseconds(match[3]) + offset
        if end <= 0:
            return ''
        return _timestamp(max(0, start)) + match[2] + _timestamp(end) + match[4]
    return _CUE.sub(cue, _MAP.sub('', text))
