"""
Tests for opt-in bare content-ID scraping (#81): sites that list raw 40-hex
hashes without the acestream:// scheme.
"""

import asyncio

from fastapi import status
from sqlalchemy import text

from app.models.url_types import RegularURL
from app.scrapers.http import HTTPScraper

ID_A = "a" * 40
ID_B = "0123456789abcdef0123456789abcdef01234567"
ID_C = "c" * 40

PAGE = f"""
<html><body>
<p>Sports One: {ID_A}</p>
<p>{ID_B}</p>
<p>Linked Channel acestream://{ID_C}</p>
<p>short hash deadbeef should be ignored</p>
</body></html>
"""


def _make_scraper(bare: bool) -> HTTPScraper:
    scraper = HTTPScraper(RegularURL("http://example.com/list"))

    async def fake_fetch(url):
        return PAGE

    scraper.fetch_content = fake_fetch
    scraper.scrape_bare_ids = bare
    # Avoid touching the DB in the URL-status update
    async def noop_update(url, status, error=None):
        return None
    scraper.update_url_status = noop_update
    return scraper


class TestBareIdExtraction:
    def test_disabled_by_default_ignores_bare_ids(self):
        scraper = _make_scraper(bare=False)
        channels, scrape_status = asyncio.run(scraper.scrape())
        ids = {c[0] for c in channels}
        assert ID_A not in ids
        assert ID_B not in ids

    def test_enabled_harvests_bare_ids_with_line_names(self):
        scraper = _make_scraper(bare=True)
        channels, scrape_status = asyncio.run(scraper.scrape())
        by_id = {c[0]: c[1] for c in channels}

        assert by_id.get(ID_A) == "Sports One"
        # No name on the line: the hash doubles as the editable name
        assert by_id.get(ID_B) == ID_B
        # acestream:// lines stay with the dedicated extractor
        assert ID_C not in by_id
        # Sub-40-hex strings never match
        assert all(len(i) == 40 for i in by_id)

    def test_already_identified_ids_are_not_duplicated(self):
        scraper = _make_scraper(bare=True)
        scraper.identified_ids.add(ID_A)
        channels = scraper.extract_bare_ids(PAGE)
        ids = {c[0] for c in channels}
        assert ID_A not in ids
        assert ID_B in ids

    def test_markup_between_name_and_hash_keeps_the_name(self):
        """Inline markup and table cells must not orphan the label."""
        id_d = "d" * 40
        id_e = "e" * 40
        id_f = "f" * 40
        page = f"""
        <table><tr><td>Sports Two</td><td>{ID_A}</td></tr>
        <tr><td>Sports Three</td><td>{id_d}</td></tr></table>
        <p><b>News HD</b>: {id_e}</p>
        <p>Movie: <code>{id_f}</code></p>
        """
        scraper = _make_scraper(bare=True)
        by_id = {c[0]: c[1] for c in scraper.extract_bare_ids(page)}
        assert by_id[ID_A] == "Sports Two"
        assert by_id[id_d] == "Sports Three"
        assert by_id[id_e] == "News HD"
        assert by_id[id_f] == "Movie"

    def test_hashes_inside_urls_and_infohashes_are_ignored(self):
        sha = "0123456789abcdef0123456789abcdef01234567"
        page = f"""
        <p>see https://github.com/o/r/commit/{sha}</p>
        <p>magnet:?xt=urn:btih:{ID_A}</p>
        <p>Good Channel: {ID_C}</p>
        """
        scraper = _make_scraper(bare=True)
        by_id = {c[0]: c[1] for c in scraper.extract_bare_ids(page)}
        assert sha not in by_id
        assert ID_A not in by_id
        assert by_id == {ID_C: "Good Channel"}

    def test_blocked_url_fails_fast_without_retries(self):
        from app.utils.url_guard import BlockedURLError

        scraper = _make_scraper(bare=False)
        attempts = []

        async def blocked_fetch(url):
            attempts.append(url)
            raise BlockedURLError("Refusing to fetch: metadata endpoint")

        scraper.fetch_content = blocked_fetch
        channels, scrape_status = asyncio.run(scraper.scrape())
        assert channels == []
        assert "Refusing to fetch" in scrape_status
        assert len(attempts) == 1


class TestBareIdUrlApi:
    def test_create_url_with_flag(self, client):
        response = client.post(
            "/api/v1/scrapers/urls",
            json={"url": "http://example.com/bare-list", "scrape_bare_ids": True},
        )
        assert response.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
        data = response.json()
        assert data["scrape_bare_ids"] is True

    def test_flag_defaults_off_and_is_updatable(self, client):
        response = client.post(
            "/api/v1/scrapers/urls",
            json={"url": "http://example.com/normal-list"},
        )
        data = response.json()
        assert data["scrape_bare_ids"] is False

        url_id = data["id"]
        response = client.patch(
            f"/api/v1/scrapers/urls/{url_id}",
            json={"scrape_bare_ids": True},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["scrape_bare_ids"] is True

    def test_list_tolerates_null_flag_left_by_the_v1_migrator(self, client, db_session):
        # The pre-2026-08-29 migrator provisioned v2 with create_all (no server
        # default) and inserted URLs with raw SQL, so every migrated row carries
        # scrape_bare_ids = NULL. Listing must not 500 on those rows.
        db_session.execute(text(
            "INSERT INTO scraped_urls "
            "(url, url_type, status, error_count, enabled, added_at, scrape_bare_ids) "
            "VALUES ('http://example.com/migrated', 'regular', 'ok', 0, 1, "
            "'2026-01-01 00:00:00', NULL)"
        ))
        db_session.commit()

        response = client.get("/api/v1/scrapers/urls")
        assert response.status_code == status.HTTP_200_OK
        rows = {row["url"]: row for row in response.json()}
        assert rows["http://example.com/migrated"]["scrape_bare_ids"] is False


def test_model_column_defaults_to_false_for_raw_inserts(test_db):
    # Raw SQL that omits the column (the v1 migrator, ad-hoc repairs) must get
    # false, not NULL, even on a schema created by Base.metadata.create_all.
    engine, _ = test_db
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO scraped_urls (url, url_type, status, error_count, enabled, added_at) "
            "VALUES ('http://example.com/raw', 'regular', 'ok', 0, 1, '2026-01-01 00:00:00')"
        ))
        flag = conn.execute(text("SELECT scrape_bare_ids FROM scraped_urls")).scalar()
    assert flag == 0
