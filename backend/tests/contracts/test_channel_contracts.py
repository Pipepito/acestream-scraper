"""Contract tests for channels and TV-channel payload schemas."""
from app.schemas.channel import (
    BulkChannelActivateRequest,
    BulkChannelEditRequest,
    TVChannelAssociationRequest,
    TVChannelBatchAssignRequest,
    TVChannelBulkEPGUpdateRequest,
)


def test_schema_models_cover_bulk_and_association_payloads():
    bulk_edit = BulkChannelEditRequest.model_validate(
        {
            "acestreamchannel_ids": ["ace-1", "ace-2"],
            "fields": {"group": "Sports", "is_active": True},
        }
    )
    assert bulk_edit.acestreamchannel_ids == ["ace-1", "ace-2"]
    assert bulk_edit.fields.group == "Sports"

    bulk_activate = BulkChannelActivateRequest.model_validate(
        {"acestreamchannel_ids": ["ace-1"], "active": False}
    )
    assert bulk_activate.active is False

    association = TVChannelAssociationRequest.model_validate(
        {"acestream_channel_id": "ace-123"}
    )
    assert association.acestream_channel_id == "ace-123"

    batch_assign = TVChannelBatchAssignRequest.model_validate(
        {"assignments": [{"tv_channel_id": 1, "acestream_channel_id": "ace-123"}]}
    )
    assert batch_assign.assignments[0].tv_channel_id == 1

    bulk_epg = TVChannelBulkEPGUpdateRequest.model_validate(
        {"updates": [{"tv_channel_id": 1, "epg_id": "epg.test.1"}]}
    )
    assert bulk_epg.updates[0].epg_id == "epg.test.1"


def test_tv_channels_list_contract(client, seed_tv_channels):
    response = client.get("/api/v1/tv-channels/")
    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"items", "total"}
    assert isinstance(payload["items"], list)
    assert isinstance(payload["total"], int)


def test_bulk_edit_contract_requires_typed_shape(client):
    # missing this required field should produce schema-level 422
    response = client.put("/api/v1/channels/bulk_edit", json={"fields": {"group": "News"}})
    assert response.status_code == 422


def test_association_contract_requires_acestream_channel_id(client, seed_tv_channels):
    tv_channel_id = seed_tv_channels[0].id
    response = client.post(f"/api/v1/tv-channels/{tv_channel_id}/acestreams", json={})
    assert response.status_code == 422
