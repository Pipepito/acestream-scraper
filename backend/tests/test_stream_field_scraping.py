"""Structured copy fields and ordinary links must not need site-specific CSS."""
import asyncio

from bs4 import BeautifulSoup
import pytest

from app.models.url_types import RegularURL
from app.scrapers.http import HTTPScraper

A = 'a' * 40
B = 'b' * 40


def extract(page, bare=False):
    scraper = HTTPScraper(RegularURL('https://example.com/channels'))
    scraper.scrape_bare_ids = bare
    return scraper.extract_from_content(BeautifulSoup(page, 'html.parser'))


def test_copy_fields_use_each_server_label_and_deduplicate_links():
    page = '<h1>Sports streams</h1>'
    for content_id, name in [(A, 'Server 1: Sports FHD'), (B, 'Server 2: News HD')]:
        page += f'''<div>{name}</div><div class="input-group">
        <input id="{content_id}" value="{content_id}" placeholder="Server 1">
        <div><button>Copy</button></div>
        <a href="acestream://{content_id}">{content_id}<br>DIRECT OPEN! CLICK AND TRY!!!</a>
        </div>'''
    assert extract(page) == [(A, 'Server 1: Sports FHD'), (B, 'Server 2: News HD')]


def test_named_links_do_not_share_first_link_name():
    assert extract(f'<a href="acestream://{A}">Sports</a><a href="acestream://{B}">News</a>') == [(A, 'Sports'), (B, 'News')]


def test_unlabelled_explicit_link_is_retained():
    assert extract(f'<a href="acestream://{A}">Play</a>') == [(A, A)]


def test_bare_input_requires_opt_in_or_stream_evidence():
    page = f'<label for="copy">Sports</label><input id="copy" value="{A}">'
    assert extract(page) == []
    assert extract(page, bare=True) == [(A, 'Sports')]
    assert extract(f'<input name="acestream" aria-label="Sports" value="{A.upper()}">') == [(A, 'Sports')]


@pytest.mark.parametrize('page', [
    f'<input type="hidden" name="acestream" value="{A}">',
    f'<input type="password" value="{A}">',
    f'<div id="{A}">Unrelated DOM ID</div>',
    f'<input value="https://example.com/commit/{A}">',
    f'<input value="magnet:?xt=urn:btih:{A}">',
    f'<input value="{A}a">',
])
def test_unrelated_or_invalid_values_are_ignored_even_when_opted_in(page):
    assert extract(page, bare=True) == []


def test_textarea_and_data_attribute():
    assert extract(f'<textarea aria-label="Sports">acestream://{A}</textarea><button data-acestream-id="{B}" title="News">Copy</button>') == [(A, 'Sports'), (B, 'News')]


def test_scrape_pipeline_extracts_fields_without_opt_in():
    scraper = HTTPScraper(RegularURL('https://example.com/channels'))
    async def fetch(url):
        return f'<input name="acestream" value="{A}" aria-label="Sports">'
    async def update(*args):
        pass
    scraper.fetch_content = fetch
    scraper.update_url_status = update
    assert asyncio.run(scraper.scrape()) == ([(A, 'Sports', {})], 'OK')
