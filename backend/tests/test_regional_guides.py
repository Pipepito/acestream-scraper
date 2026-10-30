"""Synthetic markup reproduces the interpretation cases supplied in issue #233."""
import asyncio
from datetime import date
from xml.etree import ElementTree as ET

import pytest

from app.services import sincroguia_guide as sg, tvrioja_guide as tr, regional_guides

RIOJA = 'https://proyectos.larioja.com/tvr/dimeprogramacion/dimeprogramacion.php?dia=0'
SINCRO = 'https://sincroguia-tv.expansion.com/programacion/test-channel'


def rioja(*rows):
    return ('<table>' + ''.join(f'<tr><td class="hora">{clock} h</td><td class="programa"><strong>{title}</strong> Description</td></tr>'
                              for clock, title in rows) + '</table>').encode()


def sincro(day, *rows):
    return ('<h1 class="m-top__title">Programación Test Channel</h1>'
            f'<h2 class="m-schedule-day__title">{day}</h2>' + ''.join(
                f'<div class="m-program" id="event-{i}"><h2 class="m-program__name">{title}</h2><p class="m-program__info">{start} a {end}h</p></div>'
                for i, (start, end, title) in enumerate(rows))).encode()


def test_rioja_current_week_midnight_and_seasonal_offsets():
    today = date(2026, 10, 30)
    assert tr.page_date(RIOJA, today) == today
    assert tr.page_date(RIOJA.replace('dia=0', 'dia=1'), today) == date(2026, 10, 26)
    assert tr.page_date(RIOJA.replace('dia=0', 'dia=7'), today) == date(2026, 11, 1)
    root = ET.fromstring(tr.html_to_xmltv(rioja(('12:00', 'News &amp; sport'), ('23:00', 'Film')), RIOJA, today))
    assert root.find('programme').get('start') == '20261030110000 +0000'
    assert root.findall('programme')[-1].get('stop') == '20261030230000 +0000'
    assert root.find('programme/title').text == 'News & sport'
    summer = ET.fromstring(tr.html_to_xmltv(rioja(('12:00', 'News')), RIOJA, date(2026, 7, 2)))
    assert summer.find('programme').get('start') == '20260702100000 +0000'


def test_sincro_midnight_year_boundary_and_ignores_misleading_jsonld():
    page = sincro('jueves 31 de diciembre', ('23:30', '00:30', 'Film'), ('00:30', '01:30', 'News'))
    page += b'<script type="application/ld+json">{"name":"Wrong channel"}</script>'
    root = ET.fromstring(sg.html_to_xmltv(page, SINCRO, date(2027, 1, 1)))
    rows = root.findall('programme')
    assert rows[0].get('start') == '20261231223000 +0000'
    assert rows[1].get('stop') == '20270101003000 +0000'
    assert root.find('channel').get('id') == 'sincroguia.test-channel'


@pytest.mark.parametrize('day', [date(2026, 3, 29), date(2026, 10, 25)])
def test_both_adapters_reject_ambiguous_or_nonexistent_local_time(day):
    with pytest.raises(ValueError, match='ambiguous|exist'):
        tr.html_to_xmltv(rioja(('02:30', 'News')), RIOJA, day)
    label = '29 de marzo' if day.month == 3 else '25 de octubre'
    with pytest.raises(ValueError, match='ambiguous|exist'):
        sg.html_to_xmltv(sincro(label, ('02:30', '04:00', 'News')), SINCRO, day)


@pytest.mark.parametrize('body', [b'<html>Login</html>', rioja(('25:00', 'Bad')), rioja(('12:00', 'One'), ('12:00', 'Two'))])
def test_rioja_rejects_empty_invalid_duplicate_times(body):
    with pytest.raises(ValueError):
        tr.html_to_xmltv(body, RIOJA, date(2026, 10, 30))


def test_exact_hosts_and_channel_paths_only():
    assert regional_guides.supports(RIOJA) and regional_guides.supports(SINCRO)
    assert not regional_guides.supports(SINCRO.replace('/programacion/test-channel', '/'))
    assert not regional_guides.supports(SINCRO.replace('sincroguia-tv.', 'evil.sincroguia-tv.'))


def test_week_transport_is_all_or_nothing_and_bounded(monkeypatch):
    urls = []
    status = 200
    oversized = False
    class Response:
        def __init__(self):
            self.content = self
            self.status = status
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def iter_chunked(self, size):
            yield b'x' * (2 * 1024 * 1024 + 1) if oversized else rioja(('12:00', 'News'))
    class Session(Response):
        def get(self, url, **kwargs):
            assert kwargs == {'allow_redirects': False}
            urls.append(url)
            return Response()
    monkeypatch.setattr(regional_guides, 'source_session', lambda **kw: Session())
    root = ET.fromstring(asyncio.run(regional_guides.fetch(RIOJA)))
    assert len(urls) == 7 and len(root.findall('channel')) == 1 and len(root.findall('programme')) == 7
    status = 302
    with pytest.raises(ValueError, match='unavailable'):
        asyncio.run(regional_guides.fetch(RIOJA))
    status, oversized = 200, True
    with pytest.raises(ValueError, match='2 MiB'):
        asyncio.run(regional_guides.fetch(RIOJA))
