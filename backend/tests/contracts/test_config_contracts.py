"""Contract tests for config endpoint payload/response shapes."""


def test_base_url_update_contract_accepts_alias_and_value(client):
    alias_payload = {"base_url": "http://contract-alias.example.com:8000"}
    response = client.put("/api/v1/config/base_url", json=alias_payload)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"message", "value"}
    assert data["value"] == alias_payload["base_url"]

    value_payload = {"value": "http://contract-value.example.com:8000"}
    response = client.put("/api/v1/config/base_url", json=value_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["value"] == value_payload["value"]


def test_rescrape_interval_contract_accepts_value_and_hours(client):
    response = client.put("/api/v1/config/rescrape_interval", json={"value": "5"})
    assert response.status_code == 200
    assert response.json()["value"] == "5"

    response = client.put("/api/v1/config/rescrape_interval", json={"hours": 6})
    assert response.status_code == 200
    assert response.json()["value"] == "6"


def test_generic_config_key_update_contract(client):
    response = client.put("/api/v1/config/addpid", json={"value": "true"})
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"message", "value"}
    assert data["value"] == "true"


def test_generic_config_key_contract_unknown_key(client):
    response = client.put("/api/v1/config/not-real-key", json={"value": "x"})
    assert response.status_code == 404


def test_stream_check_interval_defaults_persists_and_reschedules(client, monkeypatch):
    from unittest.mock import Mock
    from app.api.endpoints.config import task_service
    reschedule = Mock()
    monkeypatch.setattr(task_service, 'reschedule_task', reschedule)
    url = '/api/v1/config/channel_status_interval'
    assert client.get(url).json() == {'key': 'channel_status_interval', 'value': '60'}
    assert client.put(url, json={'value': '90'}).status_code == 200
    assert client.get(url).json()['value'] == '90'
    reschedule.assert_called_once_with('channel_status', 5400)
    for value in ('0', '-1', '10081', '1.5', 'nan', '', 'abc'):
        assert client.put(url, json={'value': value}).status_code == 422
    assert client.get(url).json()['value'] == '90'
