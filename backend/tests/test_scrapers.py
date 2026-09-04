"""
Integration tests for Scraper endpoints
"""

import asyncio
import pytest
import uuid
from fastapi import status
from app.models.models import (
    AcestreamChannel,
    EPGChannel,
    EPGSource,
    ScrapedURL,
    TVChannel,
)
from app.services.m3u_service import M3UService
from app.services.scraper_service import ScraperService


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

    def test_extract_channels_from_content_preserves_group_title_tvg_logo_and_tvg_id(self):
        service = M3UService()
        content = """#EXTM3U
#EXTINF:-1 tvg-id="alpha-id" tvg-logo="https://example.com/channel-logo.png" group-title="Sports",Alpha Sports
acestream://0123456789abcdef0123456789abcdef01234567
"""

        channels = service.extract_channels_from_content(content)

        assert channels == [
            (
                "0123456789abcdef0123456789abcdef01234567",
                "Alpha Sports",
                {
                    "tvg_id": "alpha-id",
                    "tvg_logo": "https://example.com/channel-logo.png",
                    "group_title": "Sports",
                },
            )
        ]

    def test_extract_channels_from_content_extgrp_group_logo_falls_back_when_tvg_logo_missing(self):
        service = M3UService()
        content = """#EXTM3U
#EXTGRP: group-title="Cinema" group-logo="https://example.com/group-logo.png"
#EXTINF:-1 tvg-id="cinema-id",Cinema One
acestream://1111111111111111111111111111111111111111
"""

        channels = service.extract_channels_from_content(content)

        assert channels == [
            (
                "1111111111111111111111111111111111111111",
                "Cinema One",
                {
                    "tvg_id": "cinema-id",
                    "group_title": "Cinema",
                    "tvg_logo": "https://example.com/group-logo.png",
                },
            )
        ]

    def test_extract_channels_from_content_extgrp_ignores_unsupported_variants(self):
        service = M3UService()
        content = """#EXTM3U
#EXTGRP: This is not a supported metadata declaration
#EXTINF:-1,Plain Channel
acestream://2222222222222222222222222222222222222222
"""

        channels = service.extract_channels_from_content(content)

        assert channels == [
            (
                "2222222222222222222222222222222222222222",
                "Plain Channel",
                {},
            )
        ]

    def test_extract_channels_from_content_extgrp_unsupported_variant_resets_group_state(self):
        service = M3UService()
        content = """#EXTM3U
#EXTGRP: group-title="Cinema" group-logo="https://example.com/group-logo.png"
#EXTINF:-1,First Cinema
acestream://5555555555555555555555555555555555555555
#EXTGRP: unsupported blob
#EXTINF:-1,Second Plain
acestream://6666666666666666666666666666666666666666
"""

        channels = service.extract_channels_from_content(content)

        assert channels[0][2] == {
            "group_title": "Cinema",
            "tvg_logo": "https://example.com/group-logo.png",
        }
        assert channels[1][2] == {}

    def test_extract_channels_from_content_extinf_group_title_does_not_inherit_other_group_logo(self):
        service = M3UService()
        content = """#EXTM3U
#EXTGRP: group-title="Cinema" group-logo="https://example.com/cinema-logo.png"
#EXTINF:-1 group-title="Sports",Sports One
acestream://7777777777777777777777777777777777777777
"""

        channels = service.extract_channels_from_content(content)

        assert channels == [
            (
                "7777777777777777777777777777777777777777",
                "Sports One",
                {"group_title": "Sports"},
            )
        ]

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

    def test_scrape_service_replaces_stale_source_channels(self, db_session, monkeypatch):
        source_url = "https://example.com/perf_replace.m3u"

        stale = AcestreamChannel(
            id="stale-channel",
            name="Stale Channel",
            source_url=source_url,
            is_active=True,
        )
        db_session.add(stale)
        db_session.commit()

        class _FakeScraper:
            async def scrape(self):
                return [("fresh-channel", "Fresh Channel", {"group_title": "News"})], "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        service = ScraperService(db_session)
        channels, scrape_status = asyncio.run(service.scrape_url(source_url, "regular"))

        assert scrape_status == "OK"
        assert len(channels) == 1
        assert channels[0].channel_id == "fresh-channel"
        assert db_session.query(AcestreamChannel).filter(AcestreamChannel.id == "stale-channel").first() is None

    def test_scrape_service_persists_extgrp_group_title_tvg_logo_and_tvg_id(self, db_session, monkeypatch):
        source_url = "https://example.com/metadata_import.m3u"
        content = """#EXTM3U
#EXTGRP: group-title="Cinema" group-logo="https://example.com/group-logo.png"
#EXTINF:-1 tvg-id="cinema-id",Cinema One
acestream://3333333333333333333333333333333333333333
#EXTINF:-1 tvg-id="direct-id" tvg-logo="https://example.com/direct-logo.png" group-title="Sports",Direct Sports
acestream://4444444444444444444444444444444444444444
"""

        class _FakeScraper:
            def __init__(self):
                from app.models.url_types import RegularURL

                self.url_obj = RegularURL(source_url)
                self.db = None
                self.epg_service = None
                self.tv_channel_service = None

            async def scrape(self):
                channels = M3UService().extract_channels_from_content(content)
                return channels, "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        service = ScraperService(db_session)
        channels, scrape_status = asyncio.run(service.scrape_url(source_url, "regular"))

        assert scrape_status == "OK"
        assert {channel.channel_id for channel in channels} == {
            "3333333333333333333333333333333333333333",
            "4444444444444444444444444444444444444444",
        }

        fallback_channel = db_session.query(AcestreamChannel).filter(
            AcestreamChannel.id == "3333333333333333333333333333333333333333"
        ).one()
        direct_channel = db_session.query(AcestreamChannel).filter(
            AcestreamChannel.id == "4444444444444444444444444444444444444444"
        ).one()

        assert fallback_channel.group == "Cinema"
        assert fallback_channel.logo == "https://example.com/group-logo.png"
        assert fallback_channel.tvg_id == "cinema-id"

        assert direct_channel.group == "Sports"
        assert direct_channel.logo == "https://example.com/direct-logo.png"
        assert direct_channel.tvg_id == "direct-id"

    def test_first_scrape_persists_new_channel_epg_association_idempotently(self, db_session, monkeypatch):
        source_url = "https://example.com/new_epg_channels.m3u"
        channel_id = "5555555555555555555555555555555555555555"
        epg_source = EPGSource(url="https://example.com/guide.xml", name="Guide")
        db_session.add(epg_source)
        db_session.flush()
        db_session.add(
            EPGChannel(
                epg_source_id=epg_source.id,
                channel_xml_id="new-channel.example",
                name="New Channel",
            )
        )
        db_session.commit()

        content = f"""#EXTM3U
#EXTINF:-1 tvg-id="new-channel.example",New Channel
acestream://{channel_id}
"""

        class _FakeScraper:
            def __init__(self):
                from app.models.url_types import RegularURL

                self.url_obj = RegularURL(source_url)
                self.db = None
                self.epg_service = None
                self.tv_channel_service = None

            async def scrape(self):
                return M3UService().extract_channels_from_content(
                    content,
                    db=self.db,
                    epg_service=self.epg_service,
                    tv_channel_service=self.tv_channel_service,
                ), "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        service = ScraperService(db_session)
        first_channels, first_status = asyncio.run(service.scrape_url(source_url, "regular"))
        second_channels, second_status = asyncio.run(service.scrape_url(source_url, "regular"))

        assert first_status == second_status == "OK"
        assert [channel.channel_id for channel in first_channels] == [channel_id]
        assert [channel.channel_id for channel in second_channels] == [channel_id]

        tv_channels = db_session.query(TVChannel).filter(
            TVChannel.epg_id == "new-channel.example"
        ).all()
        assert len(tv_channels) == 1
        persisted = db_session.query(AcestreamChannel).filter(
            AcestreamChannel.id == channel_id
        ).one()
        assert persisted.tv_channel_id == tv_channels[0].id

    def test_scrape_service_clears_stale_metadata_on_rescrape(self, db_session, monkeypatch):
        source_url = "https://example.com/stale_metadata.m3u"
        existing = AcestreamChannel(
            id="8888888888888888888888888888888888888888",
            name="Existing Channel",
            source_url=source_url,
            group="Old Group",
            logo="https://example.com/old-logo.png",
            tvg_id="old-id",
            is_active=True,
        )
        db_session.add(existing)
        db_session.commit()

        content = """#EXTM3U
#EXTINF:-1,Existing Channel
acestream://8888888888888888888888888888888888888888
"""

        class _FakeScraper:
            def __init__(self):
                from app.models.url_types import RegularURL

                self.url_obj = RegularURL(source_url)
                self.db = None
                self.epg_service = None
                self.tv_channel_service = None

            async def scrape(self):
                channels = M3UService().extract_channels_from_content(content)
                return channels, "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        service = ScraperService(db_session)
        channels, scrape_status = asyncio.run(service.scrape_url(source_url, "regular"))

        assert scrape_status == "OK"
        assert len(channels) == 1

        db_session.refresh(existing)
        assert existing.group is None
        assert existing.logo is None
        assert existing.tvg_id is None

    def test_scrape_service_keeps_existing_channels_when_empty_scrape_returns_ok(self, db_session, monkeypatch):
        source_url = "https://example.com/empty_scrape.m3u"
        existing = AcestreamChannel(
            id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            name="Existing Channel",
            source_url=source_url,
            is_active=True,
        )
        db_session.add(existing)
        db_session.commit()

        class _FakeScraper:
            def __init__(self):
                from app.models.url_types import RegularURL

                self.url_obj = RegularURL(source_url)
                self.db = None
                self.epg_service = None
                self.tv_channel_service = None

            async def scrape(self):
                return [], "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        service = ScraperService(db_session)
        channels, scrape_status = asyncio.run(service.scrape_url(source_url, "regular"))

        assert scrape_status == "OK"
        assert channels == []
        assert db_session.query(AcestreamChannel).filter(AcestreamChannel.id == existing.id).one_or_none() is not None

    def test_scrape_service_persists_channels_under_normalized_url(self, db_session, monkeypatch):
        input_url = "http://example.com:43110/channel-list"
        normalized_url = "zero://channel-list"

        class _FakeScraper:
            def __init__(self):
                from app.models.url_types import ZeronetURL

                self.url_obj = ZeronetURL(input_url)
                self.db = None
                self.epg_service = None
                self.tv_channel_service = None

            async def scrape(self):
                return [
                    (
                        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                        "Normalized Channel",
                        {"group_title": "Sports"},
                    )
                ], "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        service = ScraperService(db_session)
        channels, scrape_status = asyncio.run(service.scrape_url(input_url, "auto"))

        assert scrape_status == "OK"
        assert len(channels) == 1
        persisted = db_session.query(AcestreamChannel).filter(
            AcestreamChannel.id == "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        ).one()
        assert persisted.source_url == normalized_url

    def test_get_scraped_urls_counts_channels_by_normalized_url(self, db_session):
        scraped_url = ScrapedURL(url="http://example.com:43110/channel-list", url_type="auto", status="active", enabled=True)
        db_session.add(scraped_url)
        db_session.flush()
        db_session.add(
            AcestreamChannel(
                id="dddddddddddddddddddddddddddddddddddddddd",
                name="Counted Channel",
                source_url="zero://channel-list",
                is_active=True,
            )
        )
        db_session.commit()

        rows = ScraperService(db_session).get_scraped_urls()

        assert len(rows) == 1
        assert rows[0].channels_found == 1

    def test_get_scraped_urls_does_not_double_count_regular_urls(self, db_session):
        scraped_url = ScrapedURL(url="https://example.com/playlist.m3u", url_type="regular", status="active", enabled=True)
        db_session.add(scraped_url)
        db_session.flush()
        db_session.add(
            AcestreamChannel(
                id="eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                name="Regular Counted Channel",
                source_url="https://example.com/playlist.m3u",
                is_active=True,
            )
        )
        db_session.commit()

        rows = ScraperService(db_session).get_scraped_urls()

        assert len(rows) == 1
        assert rows[0].channels_found == 1

    def test_scrape_service_removes_legacy_original_url_channels_after_normalized_rescrape(self, db_session, monkeypatch):
        input_url = "http://example.com:43110/channel-list"
        normalized_url = "zero://channel-list"
        db_session.add(
            AcestreamChannel(
                id="ffffffffffffffffffffffffffffffffffffffff",
                name="Legacy Channel",
                source_url=input_url,
                is_active=True,
            )
        )
        db_session.commit()

        class _FakeScraper:
            def __init__(self):
                from app.models.url_types import ZeronetURL

                self.url_obj = ZeronetURL(input_url)
                self.db = None
                self.epg_service = None
                self.tv_channel_service = None

            async def scrape(self):
                return [
                    (
                        "1212121212121212121212121212121212121212",
                        "Fresh Normalized",
                        {},
                    )
                ], "OK"

        monkeypatch.setattr(
            "app.services.scraper_service.create_scraper_for_url",
            lambda _url, _url_type: _FakeScraper(),
        )

        channels, scrape_status = asyncio.run(ScraperService(db_session).scrape_url(input_url, "auto"))

        assert scrape_status == "OK"
        assert len(channels) == 1
        assert db_session.query(AcestreamChannel).filter(AcestreamChannel.id == "ffffffffffffffffffffffffffffffffffffffff").one_or_none() is None
        persisted = db_session.query(AcestreamChannel).filter(
            AcestreamChannel.id == "1212121212121212121212121212121212121212"
        ).one()
        assert persisted.source_url == normalized_url

    def test_base_scraper_updates_existing_scraped_url_status_without_creating_normalized_duplicate(self, db_session):
        from app.models.url_types import ZeronetURL
        from app.scrapers.base import BaseScraper

        original_url = "http://example.com:43110/channel-list"
        normalized_url = "zero://channel-list"
        existing = ScrapedURL(url=original_url, url_type="auto", status="pending", enabled=True)
        db_session.add(existing)
        db_session.commit()

        class _FakeScraper(BaseScraper):
            async def fetch_content(self, url: str) -> str:
                return ""

        scraper = _FakeScraper(ZeronetURL(original_url), db=db_session)
        asyncio.run(scraper.update_url_status(normalized_url, "OK"))

        db_session.expire_all()
        rows = db_session.query(ScrapedURL).order_by(ScrapedURL.id.asc()).all()
        assert len(rows) == 1
        assert rows[0].url == original_url
        assert rows[0].status == "OK"

    def test_base_scraper_extracts_linked_m3u_metadata(self):
        from app.models.url_types import RegularURL
        from app.scrapers.base import BaseScraper

        class _FakeScraper(BaseScraper):
            async def fetch_content(self, url: str) -> str:
                if url == "https://example.com/page":
                    return '<a href="https://example.com/list.m3u">Playlist</a>'
                if url == "https://example.com/list.m3u":
                    return """#EXTM3U
#EXTGRP: group-title="Cinema" group-logo="https://example.com/group-logo.png"
#EXTINF:-1 tvg-id="linked-id",Linked Channel
acestream://9999999999999999999999999999999999999999
"""
                raise AssertionError(f"Unexpected URL: {url}")

        scraper = _FakeScraper(RegularURL(url="https://example.com/page"))
        channels, status = asyncio.run(scraper.scrape())

        assert status == "OK"
        assert channels == [
            (
                "9999999999999999999999999999999999999999",
                "Linked Channel",
                {
                    "tvg_id": "linked-id",
                    "group_title": "Cinema",
                    "tvg_logo": "https://example.com/group-logo.png",
                },
            )
        ]

    def test_base_scraper_resolves_relative_m3u_links_for_zeronet_normalized_sources(self):
        from app.models.url_types import ZeronetURL
        from app.scrapers.base import BaseScraper

        class _FakeScraper(BaseScraper):
            async def fetch_content(self, url: str) -> str:
                if url == "zero://site/path":
                    return '<a href="channels/list.m3u">Playlist</a>'
                if url == "zero://site/channels/list.m3u":
                    return """#EXTM3U
#EXTINF:-1 tvg-id="zero-id",Zero Channel
acestream://cccccccccccccccccccccccccccccccccccccccc
"""
                raise AssertionError(f"Unexpected URL: {url}")

        scraper = _FakeScraper(ZeronetURL("zero://site/path"))
        channels, status = asyncio.run(scraper.scrape())

        assert status == "OK"
        assert channels == [
            (
                "cccccccccccccccccccccccccccccccccccccccc",
                "Zero Channel",
                {"tvg_id": "zero-id"},
            )
        ]
