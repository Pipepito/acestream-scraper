import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

from app.models.models import AcestreamChannel, EPGChannel, EPGProgram, EPGSource, TVChannel


PARITY_DIR = Path(__file__).parent
SNAPSHOT_PATH = PARITY_DIR / "snapshots" / "output_validity_snapshot.json"


def _load_output_snapshot():
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _seed_output_parity_data(db_session):
    channel_alpha = AcestreamChannel(
        id="5555555555555555555555555555555555555555",
        name="Parity Output Alpha",
        group="Parity Group",
        logo="https://cdn.example.com/output-alpha.png",
        tvg_id="parity.output.alpha",
        tvg_name="Parity Output Alpha",
        source_url="https://example.com/output/alpha.m3u",
        is_active=True,
        is_online=True,
    )
    channel_beta = AcestreamChannel(
        id="6666666666666666666666666666666666666666",
        name="Parity Output Beta",
        group="Parity Group",
        logo="https://cdn.example.com/output-beta.png",
        tvg_id="parity.output.beta",
        tvg_name="Parity Output Beta",
        source_url="https://example.com/output/beta.m3u",
        is_active=True,
        is_online=True,
    )

    source = EPGSource(
        url="https://example.com/epg/parity.xml",
        name="Parity Source",
        enabled=True,
    )
    db_session.add_all([channel_alpha, channel_beta, source])
    db_session.flush()

    tv_channel = TVChannel(
        name="Parity TV Alpha",
        epg_id="parity.output.alpha",
        epg_source_id=source.id,
        logo_url="https://cdn.example.com/output-alpha.png",
        is_active=True,
        is_favorite=True,
        channel_number=1,
    )
    db_session.add(tv_channel)
    db_session.flush()

    epg_channel = EPGChannel(
        epg_source_id=source.id,
        channel_xml_id="parity.output.alpha",
        name="Parity TV Alpha",
    )
    db_session.add(epg_channel)
    db_session.flush()

    start = datetime.utcnow() - timedelta(minutes=15)
    end = start + timedelta(minutes=45)
    program = EPGProgram(
        epg_channel_id=epg_channel.id,
        start_time=start,
        end_time=end,
        title="Parity Program",
        subtitle="Episode 1",
        description="Parity validation broadcast.",
        category="News",
    )
    db_session.add(program)
    db_session.commit()


def test_playlist_output_validity_and_snapshot(client, db_session):
    _seed_output_parity_data(db_session)
    snapshot = _load_output_snapshot()["playlist"]

    response = client.get("/api/v1/playlists/m3u?only_online=false")
    assert response.status_code == 200

    content = response.text
    assert content.startswith(snapshot["header"])

    for expected_name in snapshot["expected_names"]:
        assert expected_name in content

    for required_attr in snapshot["required_attributes"]:
        assert required_attr in content


def test_epg_xml_output_validity_and_snapshot(client, db_session):
    _seed_output_parity_data(db_session)
    snapshot = _load_output_snapshot()["epg"]

    response = client.get("/api/v1/epg/xml")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    xml_root = ET.fromstring(response.text)
    assert xml_root.tag == snapshot["required_root_tag"]

    xml_channel_ids = {item.attrib["id"] for item in xml_root.findall("./channel")}
    for channel_id in snapshot["expected_channel_ids"]:
        assert channel_id in xml_channel_ids

    xml_titles = {item.text for item in xml_root.findall("./programme/title")}
    for title in snapshot["expected_program_titles"]:
        assert title in xml_titles
