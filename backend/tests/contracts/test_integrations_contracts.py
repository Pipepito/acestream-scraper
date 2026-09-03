"""Contract tests for the media-integration payload shapes (spec 4.3, 5.1).

Key sets rather than values: these pin the JSON the OpenAPI document and the
frontend's generated types are built from, so a renamed or dropped field fails
here before it reaches a browser.
"""
import pytest
from pydantic import ValidationError

from app.schemas.player import PlayerSessionCreate


@pytest.mark.parametrize("content_id", ["0" * 40, "a" * 40, "F" * 40, "0123456789abcdefABCDEF" + "0" * 18])
def test_player_session_create_accepts_40_hex(content_id):
    assert PlayerSessionCreate(content_id=content_id).content_id == content_id


@pytest.mark.parametrize("content_id", ["", "0" * 39, "0" * 41, "g" * 40, "0" * 39 + "-", " " + "0" * 40])
def test_player_session_create_rejects_anything_else(content_id):
    with pytest.raises(ValidationError):
        PlayerSessionCreate(content_id=content_id)


def test_player_session_create_rejects_a_bad_content_id_over_http(client):
    assert client.post("/api/v1/player/sessions", json={"content_id": "nope"}).status_code == 422


def test_player_capabilities_response_contract(client):
    response = client.get("/api/v1/player/capabilities")
    assert response.status_code == 200
    assert set(response.json()) == {"ffmpeg_available", "ffmpeg_path", "max_sessions", "hls_dir"}


def test_player_sessions_response_contract(client):
    response = client.get("/api/v1/player/sessions")
    assert response.status_code == 200
    assert set(response.json()) == {"sessions"}


def test_public_url_response_contract(client):
    response = client.get("/api/v1/system/public-url")
    assert response.status_code == 200
    assert set(response.json()) == {"url", "source", "warnings"}
