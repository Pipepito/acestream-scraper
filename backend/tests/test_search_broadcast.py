from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from app.models.models import AcestreamChannel
from app.services.channel_status_service import ChannelStatusService


def test_search_probe_validates_hash_before_engine_call(client, monkeypatch):
    probe = AsyncMock()
    monkeypatch.setattr(ChannelStatusService, 'check_channel_status', probe)
    response = client.post('/api/v1/search/not-a-hash/check_status')
    assert response.status_code == 422
    probe.assert_not_called()


def test_search_probe_uses_infohash_without_adding_or_updating_inventory(client, db_session, monkeypatch):
    channel = AcestreamChannel(id='a' * 40, name='Saved', is_online=False)
    db_session.add(channel)
    db_session.commit()
    result = {'channel_id': 'a' * 40, 'is_online': True, 'status': 'online',
              'message': 'Broadcast data is arriving', 'last_checked': datetime.now(timezone.utc), 'error': None}
    probe = AsyncMock(return_value=result)
    monkeypatch.setattr(ChannelStatusService, 'check_channel_status', probe)
    response = client.post('/api/v1/search/' + 'A' * 40 + '/check_status')
    assert response.status_code == 200
    assert response.json()['is_online'] is True
    assert probe.call_args.kwargs == {'identifier': 'infohash', 'persist': False}
    assert probe.call_args.args[0].id == 'a' * 40
    db_session.refresh(channel)
    assert channel.is_online is False
    assert db_session.query(AcestreamChannel).count() == 1


@pytest.mark.parametrize('grouped', [True, False])
def test_catalogue_status_passes_through_endpoint(client, monkeypatch, grouped):
    item = {'name': 'Example', 'infohash': 'a' * 40, 'status': 1,
            'availability': 1, 'availability_updated_at': 1788614461}
    results = [{'name': 'Example', 'items': [item]}] if grouped else [item]
    response = Mock(status_code=200, text='{}')
    response.json.return_value = {'result': {'results': results, 'total': 1}}
    monkeypatch.setattr('app.services.search_service.requests.get', Mock(return_value=response))
    data = client.get('/api/v1/search?query=Example').json()['results'][0]
    assert data['status'] == 1
    assert data['availability_updated_at'] == 1788614461
    assert data['availability'] == 1
    assert 'is_online' not in data
