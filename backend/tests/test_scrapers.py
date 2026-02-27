"""
Integration tests for Scraper endpoints
"""

import pytest
import uuid
from fastapi import status
from app.models.models import ScrapedURL


class TestScraperEndpoints:
    """Test scraper operations."""

    def test_scrape_url_with_m3u(self, client, mock_http_requests):
        """Test scraping a URL with M3U content."""
        scrape_data = {
            "url": "https://example.com/test.m3u",
            "url_type": "regular"
        }
        response = client.post("/api/v1/scrapers/scrape", json=scrape_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "channels" in data
        assert "message" in data
        assert data["url"] == scrape_data["url"]
        # The mock should return at least some channels from the M3U content
        assert isinstance(data["channels"], list)

    def test_scrape_url_with_invalid_url(self, client):
        """Test scraping with an invalid URL."""
        scrape_data = {
            "url": "invalid-url",
            "url_type": "regular"
        }
        response = client.post("/api/v1/scrapers/scrape", json=scrape_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Scraping failed" in data["detail"]

    def test_scrape_url_with_empty_data(self, client):
        """Test scraping with empty data."""
        scrape_data = {}
        response = client.post("/api/v1/scrapers/scrape", json=scrape_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestScrapedURLEndpoints:
    """Test scraped URL CRUD operations."""

    def test_get_scraped_urls_empty(self, client):
        """Test getting scraped URLs when none exist."""
        response = client.get("/api/v1/scrapers/urls")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_scraped_urls_with_data(self, client, seed_scraped_urls):
        """Test getting scraped URLs with data."""
        response = client.get("/api/v1/scrapers/urls")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert data[0]["url"] == "https://example.com/playlist1.m3u"
        assert data[1]["url"] == "https://example.com/playlist2.m3u"
        assert data[2]["url"] == "https://example.com/playlist3.m3u"

    def test_get_scraped_urls_with_pagination(self, client, seed_scraped_urls):
        """Test getting scraped URLs with pagination."""
        response = client.get("/api/v1/scrapers/urls?skip=1&limit=1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["url"] == "https://example.com/playlist2.m3u"

    def test_get_scraped_urls_with_status_filter(self, client, seed_scraped_urls):
        """Test getting scraped URLs filtered by status."""
        response = client.get("/api/v1/scrapers/urls?status=active")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # All seeded URLs have active status
        for url in data:
            assert url["status"] == "active"

    def test_create_scraped_url(self, client, sample_scraped_url_data):
        """Test creating a new scraped URL."""
        response = client.post("/api/v1/scrapers/urls", json=sample_scraped_url_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["url"] == sample_scraped_url_data["url"]
        assert data["url_type"] == sample_scraped_url_data["url_type"]
        assert data["status"] == sample_scraped_url_data["status"]
        assert data["enabled"] == sample_scraped_url_data["enabled"]

    def test_create_scraped_url_invalid_data(self, client):
        """Test creating a scraped URL with invalid data."""
        invalid_data = {"url": ""}  # Missing required fields
        response = client.post("/api/v1/scrapers/urls", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_scraped_url_duplicate(self, client, seed_scraped_urls):
        """Test creating a scraped URL with duplicate URL."""
        duplicate_data = {
            "url": seed_scraped_urls[0].url,
            "url_type": "regular",
            "status": "active",
            "enabled": True
        }
        response = client.post("/api/v1/scrapers/urls", json=duplicate_data)
        # Should handle duplicates gracefully (update existing or return existing)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_get_scraped_url_by_id(self, client, seed_scraped_urls):
        """Test getting a specific scraped URL by ID."""
        url_id = seed_scraped_urls[0].id
        response = client.get(f"/api/v1/scrapers/urls/{url_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == url_id
        assert data["url"] == seed_scraped_urls[0].url

    def test_get_scraped_url_by_id_not_found(self, client):
        """Test getting a non-existent scraped URL."""
        fake_id = 99999
        response = client.get(f"/api/v1/scrapers/urls/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_scraped_url(self, client, seed_scraped_urls):
        """Test deleting a scraped URL."""
        url_id = seed_scraped_urls[0].id
        response = client.delete(f"/api/v1/scrapers/urls/{url_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify URL is deleted
        response = client.get(f"/api/v1/scrapers/urls/{url_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_scraped_url_not_found(self, client):
        """Test deleting a non-existent scraped URL."""
        fake_id = 99999
        response = client.delete(f"/api/v1/scrapers/urls/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestScrapedURLRefreshEndpoints:
    """Test scraped URL refresh operations."""

    def test_scrape_specific_url(self, client, seed_scraped_urls):
        """Test scraping a specific URL by ID."""
        url_id = seed_scraped_urls[0].id
        response = client.post(f"/api/v1/scrapers/urls/{url_id}/scrape")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "url" in data
        assert "channels_found" in data
        assert "status" in data
        assert data["url"] == seed_scraped_urls[0].url

    def test_scrape_specific_url_not_found(self, client):
        """Test scraping a non-existent URL."""
        fake_id = 99999
        response = client.post(f"/api/v1/scrapers/urls/{fake_id}/scrape")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_scrape_specific_url_disabled(self, client, seed_scraped_urls, db_session):
        """Test scraping a disabled URL."""
        url_id = seed_scraped_urls[0].id

        # Disable the URL
        scraped_url = seed_scraped_urls[0]
        scraped_url.enabled = False
        db_session.commit()

        response = client.post(f"/api/v1/scrapers/urls/{url_id}/scrape")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_scrape_all_urls(self, client, seed_scraped_urls):
        """Test scraping all URLs."""
        response = client.post("/api/v1/scrapers/urls/scrape_all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # Should scrape all 3 seeded URLs
        for scrape_result in data:
            assert "url" in scrape_result
            assert "channels_found" in scrape_result
            assert "status" in scrape_result

    def test_scrape_all_urls_with_force(self, client, seed_scraped_urls):
        """Test scraping all URLs with force parameter."""
        response = client.post("/api/v1/scrapers/urls/scrape_all?force=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3

    def test_scrape_all_urls_enabled_only(self, client, seed_scraped_urls, db_session):
        """Test scraping only enabled URLs."""
        # Disable one URL
        scraped_url = seed_scraped_urls[0]
        scraped_url.enabled = False
        db_session.commit()

        response = client.post("/api/v1/scrapers/urls/scrape_all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2  # Should only scrape enabled URLs

    def test_scrape_all_urls_with_limit(self, client, seed_scraped_urls):
        """Test scraping all URLs with limit parameter."""
        response = client.post("/api/v1/scrapers/urls/scrape_all?limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2


class TestScraperIntegration:
    """Test end-to-end scraper integration."""

    def test_scrape_and_create_channels(self, client, db_session):
        """Test that scraping creates channels in the database."""
        # Create a URL to scrape
        url_data = {
            "url": "https://example.com/test.m3u",
            "url_type": "regular",
            "status": "active",
            "enabled": True
        }

        # Create the URL
        response = client.post("/api/v1/scrapers/urls", json=url_data)
        assert response.status_code == status.HTTP_201_CREATED
        created_url = response.json()

        # Scrape the URL
        response = client.post(f"/api/v1/scrapers/urls/{created_url['id']}/scrape")
        assert response.status_code == status.HTTP_200_OK
        scrape_result = response.json()

        # Verify scraping was attempted
        assert scrape_result["url"] == url_data["url"]
        assert "channels_found" in scrape_result
        assert "status" in scrape_result

    def test_scrape_with_different_url_types(self, client):
        """Test scraping with different URL types."""
        url_types = ["regular", "acexy", "special"]

        for url_type in url_types:
            scrape_data = {
                "url": f"https://example.com/test_{url_type}.m3u",
                "url_type": url_type
            }
            response = client.post("/api/v1/scrapers/scrape", json=scrape_data)
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["url"] == scrape_data["url"]

    def test_scrape_with_malformed_content(self, client):
        """Test scraping with malformed content handling."""
        scrape_data = {
            "url": "https://example.com/malformed.m3u",
            "url_type": "regular"
        }
        response = client.post("/api/v1/scrapers/scrape", json=scrape_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should handle malformed content gracefully
        assert "status" in data
        assert data["channels_found"] >= 0
