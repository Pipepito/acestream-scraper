"""Contract tests for URL refresh endpoints."""


def test_refresh_url_contract_success(client, seed_scraped_urls):
    url_id = seed_scraped_urls[0].id
    response = client.post(f"/api/v1/urls/{url_id}/refresh")

    assert response.status_code == 202
    payload = response.json()
    assert payload["success"] is True
    assert "message" in payload


def test_refresh_url_contract_not_found(client):
    response = client.post("/api/v1/urls/999999/refresh")

    assert response.status_code == 404
    payload = response.json()
    assert payload["detail"] == "URL not found or refresh failed"


def test_refresh_all_urls_contract_shape(client, seed_scraped_urls):
    response = client.post("/api/v1/urls/refresh-all")

    assert response.status_code == 202
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["count"], int)
    assert "message" in payload
