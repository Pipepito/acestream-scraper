"""The recorded XMLTV export: one fixed guide, and the clock it was built under.

``fixtures/epg_xml_export.xml`` beside this module is the document
``EPGService.generate_epg_xml()`` produced for :func:`seed_recorded_guide`
*before* the tuner refactor split the method into ``epg_channel_lookup`` /
``programs_in_window`` / ``programme_xml_lines`` (backend/app/services/
epg_service.py at f41f630). Comparing today's output against it is what makes
a change to those shared helpers visible instead of silent.

Regenerating it is only ever right when the export is *meant* to change: seed a
session with :func:`seed_recorded_guide`, freeze the clock with
:func:`frozen_epg_clock`, and write ``generate_epg_xml()`` back to the file.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

#: The document ``generate_epg_xml()`` must keep producing for this guide.
RECORDED_EXPORT = Path(__file__).resolve().parent / "fixtures" / "epg_xml_export.xml"

#: The export window is relative to "now", so the recording needs a fixed one.
FROZEN_NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)


def frozen_epg_clock(monkeypatch) -> None:
    """Pin ``datetime.now()`` inside the EPG service to :data:`FROZEN_NOW`.

    ``generate_epg_xml`` selects programs relative to the current time, so
    without this the recorded document would only match on one day.
    """
    from app.services import epg_service

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return FROZEN_NOW if tz is not None else FROZEN_NOW.replace(tzinfo=None)

    monkeypatch.setattr(epg_service, "datetime", _FrozenDatetime)


def seed_recorded_guide(session) -> None:
    """Seed the guide the recorded document was made from.

    It deliberately covers what the export has to decide: channel ordering
    (numbered channels by number, unnumbered last by name), a TV channel whose
    ``epg_id`` matches no EPG channel, a channel with and without a logo, a
    program with every optional field and one with none, characters that must
    be escaped, and a program outside the export window.
    """
    from app.models.models import EPGChannel, EPGProgram, EPGSource, TVChannel

    source = EPGSource(name="Recorded EPG", url="https://example.com/guide.xml", enabled=True)
    session.add(source)
    session.commit()

    channels = [
        # (name, channel_number, logo_url, epg_id)
        ("Cine Uno", 1, None, "cine.uno"),
        ("News & Sport HD", 3, "https://example.com/logo-news.png?w=64&h=64", "news.hd"),
        ("Zeta Documentales", None, "https://example.com/logo-zeta.png", "zeta.tv"),
        ("Sin Guia", 2, None, "missing.from.source"),  # no EPG channel: stays out
    ]
    for name, number, logo, epg_id in channels:
        session.add(TVChannel(
            name=name,
            channel_number=number,
            logo_url=logo,
            epg_id=epg_id,
            epg_source_id=source.id,
            is_active=True,
        ))

    for xml_id, name in [("cine.uno", "Cine Uno"), ("news.hd", "News & Sport HD"), ("zeta.tv", "Zeta")]:
        session.add(EPGChannel(
            epg_source_id=source.id,
            channel_xml_id=xml_id,
            name=name,
            language="es",
        ))
    session.commit()

    by_xml_id = {
        channel.channel_xml_id: channel.id
        for channel in session.query(EPGChannel).filter(EPGChannel.epg_source_id == source.id).all()
    }

    programs = [
        # (epg channel, hours from FROZEN_NOW, duration hours, title, subtitle, description, category, image)
        ("cine.uno", 1, 2, "La Pelicula", None, None, None, None),
        ("news.hd", -2, 1, "Noticias 1 & 2", "Edicion matinal", "Titulares <en directo>", "News", "https://example.com/news.png"),
        ("news.hd", 0, 1, "Deportes", None, "Resumen de la jornada", "Sports", None),
        ("zeta.tv", 3, 1, "Naturaleza", None, None, "Documentary", None),
        # Nine days out: past days_forward=7, so the export must drop it.
        ("zeta.tv", 24 * 9, 1, "Fuera de ventana", None, None, None, None),
    ]
    for xml_id, offset_hours, duration_hours, title, subtitle, description, category, image in programs:
        start = FROZEN_NOW + timedelta(hours=offset_hours)
        session.add(EPGProgram(
            epg_channel_id=by_xml_id[xml_id],
            program_xml_id=f"{xml_id}-{offset_hours}",
            start_time=start,
            end_time=start + timedelta(hours=duration_hours),
            title=title,
            subtitle=subtitle,
            description=description,
            category=category,
            image_url=image,
        ))
    session.commit()
