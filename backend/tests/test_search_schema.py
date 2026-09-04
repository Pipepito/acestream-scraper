"""Regression tests for the search response schema."""

import pytest
from pydantic import ValidationError

from app.schemas.search import SearchResponse, SearchResultItem


class TestSearchResultItemName:
    """A numeric channel name must not break the response.

    The AceStream engine catalogue returns purely numeric names as JSON
    numbers. `name: str` rejected them, and because FastAPI validates the
    whole response, one such entry returned 500 for every query whose page
    contained it.
    """

    def test_numeric_name_is_coerced(self):
        item = SearchResultItem(id="a" * 40, name=777)
        assert item.name == "777"

    def test_float_name_is_coerced(self):
        item = SearchResultItem(id="b" * 40, name=40.5)
        assert item.name == "40.5"

    def test_string_name_is_untouched(self):
        item = SearchResultItem(id="c" * 40, name="M. LaLiga")
        assert item.name == "M. LaLiga"

    def test_missing_name_still_rejected(self):
        with pytest.raises(ValidationError):
            SearchResultItem(id="d" * 40)

    def test_whole_response_with_a_numeric_name(self):
        """This is the shape that produced the 500."""
        payload = {
            "success": True,
            "message": "Search successful",
            "results": [
                {"id": "e" * 40, "name": "M. LaLiga", "bitrate": 800000,
                 "categories": ["sport"]},
                {"id": "f" * 40, "name": 777, "bitrate": 800000,
                 "categories": []},
            ],
            "pagination": {"page": 1, "page_size": 100,
                           "total_results": 2, "total_pages": 1},
        }
        response = SearchResponse(**payload)
        assert [r.name for r in response.results] == ["M. LaLiga", "777"]
