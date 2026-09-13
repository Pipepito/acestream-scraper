"""Regression tests migrated from legacy root test suite."""

from app.models.models import ScrapedURL
from app.models.url_types import RegularURL, ZeronetURL, create_url_object


def test_scraped_url_update_status_tracks_failures():
    url = ScrapedURL(url="http://example.com", status="pending", error_count=0)

    url.update_status("success")
    assert url.status == "success"
    assert url.error_count == 0
    assert url.last_error is None

    url.update_status("failed", "network timeout")
    assert url.status == "failed"
    assert url.error_count == 1
    assert url.last_error == "network timeout"


def test_url_type_auto_detection_parity():
    regular = create_url_object("https://example.com/playlist.m3u")
    zeronet = create_url_object("zero://1abc2def3ghi")

    assert isinstance(regular, RegularURL)
    assert isinstance(zeronet, ZeronetURL)
    assert zeronet.get_internal_url() == "http://127.0.0.1:43110/1abc2def3ghi"


def test_explicit_zeronet_type_keeps_user_url_for_manual_overrides():
    url_obj = create_url_object("http://example.com/custom", url_type="zeronet")

    assert isinstance(url_obj, ZeronetURL)
    assert url_obj.get_normalized_url() == "http://example.com/custom"
