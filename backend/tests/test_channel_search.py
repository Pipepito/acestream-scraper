"""Regression coverage for channel name/ID searches and canonical list routes."""

import pytest


FIRST_ID = "deadbeef" + "1" * 32
SECOND_ID = "deadbeef" + "2" * 32
THIRD_ID = "3" * 40
SEARCH_METHODS = [
    "get_channels",
    "get_filtered_channels",
    "get_unassigned_channels",
    "get_advanced_filtered_channels",
    "get_advanced_filtered_channels_with_total",
]


@pytest.fixture
def searchable_channels(db_session, sample_channel_data):
    from app.models.models import AcestreamChannel

    channels = [
        AcestreamChannel(**{
            **sample_channel_data, "id": channel_id, "name": name, "group": group,
        })
        for channel_id, name, group in [
            (FIRST_ID, "Alpha deadbeef", "Sports"),
            (SECOND_ID, "Beta", "Sports"),
            (THIRD_ID, "Deadbeef News", "News"),
        ]
    ]
    db_session.add_all(channels)
    db_session.commit()
    return channels


@pytest.mark.parametrize("method", SEARCH_METHODS)
@pytest.mark.parametrize(("search", "expected_ids"), [
    pytest.param(FIRST_ID, [FIRST_ID], id="full-id"),
    pytest.param("beef1111", [FIRST_ID], id="partial-id"),
    pytest.param(FIRST_ID.upper(), [FIRST_ID], id="uppercase-id"),
    pytest.param("aLpHa", [FIRST_ID], id="name"),
    pytest.param("DEADBEEF", [FIRST_ID, SECOND_ID, THIRD_ID], id="name-or-id"),
    pytest.param("no-such-channel", [], id="no-match"),
])
def test_repository_searches_names_and_ids(
    db_session, searchable_channels, method, search, expected_ids,
):
    from app.repositories.channel_repository import ChannelRepository

    result = getattr(ChannelRepository(db_session), method)(search=search)
    if method == "get_advanced_filtered_channels_with_total":
        result, total = result
        assert total == len(expected_ids)
    # The first channel matches both fields for DEADBEEF, but must appear once.
    assert sorted(channel.id for channel in result) == sorted(expected_ids)


def test_unassigned_search_excludes_owned_id_matches(
    db_session, searchable_channels, seed_tv_channels,
):
    from app.repositories.channel_repository import ChannelRepository

    searchable_channels[0].tv_channel_id = seed_tv_channels[0].id
    db_session.commit()

    channels = ChannelRepository(db_session).get_unassigned_channels(search=FIRST_ID)
    assert channels == []


@pytest.mark.parametrize("path", ["/api/v1/channels/", "/api/v1/acestream-channels/"])
def test_id_search_paginates_with_filtered_total(client, searchable_channels, path):
    found = []
    for page in range(1, 4):
        response = client.get(
            path, params={"search": "DEADBEEF", "page": page, "page_size": 1},
            follow_redirects=False,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 3
        assert len(payload["items"]) == 1
        found.append(payload["items"][0]["id"])
    assert sorted(found) == sorted([FIRST_ID, SECOND_ID, THIRD_ID])

    response = client.get(
        path, params={"search": "DEADBEEF", "page": 4, "page_size": 1},
    )
    assert response.json() == {"items": [], "total": 3}


@pytest.mark.parametrize("path", ["/api/v1/channels/", "/api/v1/acestream-channels/"])
@pytest.mark.parametrize(("filters", "expected_ids"), [
    ({"group": "Sports"}, [FIRST_ID, SECOND_ID]),
    ({"group": "Missing"}, []),
    ({"is_active": True}, [SECOND_ID, THIRD_ID]),
    ({"is_active": False}, [FIRST_ID]),
    ({"is_online": True}, [SECOND_ID, THIRD_ID]),
    ({"is_online": False}, [FIRST_ID]),
    ({"assigned": True}, [FIRST_ID]),
    ({"assigned": False}, [SECOND_ID, THIRD_ID]),
    ({"group": "Sports", "is_active": True, "is_online": True, "assigned": False},
     [SECOND_ID]),
])
def test_search_preserves_other_filters(
    client, db_session, searchable_channels, seed_tv_channels, path, filters, expected_ids,
):
    target = searchable_channels[0]
    target.is_active = False
    target.is_online = False
    target.tv_channel_id = seed_tv_channels[0].id
    db_session.commit()

    response = client.get(path, params={"search": "DEADBEEF", **filters})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == len(expected_ids)
    assert sorted(channel["id"] for channel in payload["items"]) == sorted(expected_ids)


def test_create_channel_at_canonical_path_without_redirect(client, sample_channel_data):
    response = client.post(
        "/api/v1/acestream-channels/", json={**sample_channel_data, "id": FIRST_ID},
        follow_redirects=False,
    )
    assert response.status_code == 201
    assert response.json()["id"] == FIRST_ID
