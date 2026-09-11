"""Architecture guard tests for endpoint/service/repository boundaries."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_target_endpoints_do_not_query_orm_directly():
    # Core rule for this phase: endpoints should delegate persistence access.
    endpoint_files = [
        "app/api/endpoints/urls.py",
        "app/api/endpoints/scrapers.py",
        "app/api/endpoints/health.py",
    ]
    for rel_path in endpoint_files:
        contents = _read(rel_path)
        assert "db.query(" not in contents, f"Direct ORM query found in {rel_path}"


def test_url_service_uses_repository_boundary():
    contents = _read("app/services/url_service.py")
    assert "URLRepository" in contents
    assert "db.query(" not in contents


def test_stats_service_uses_repository_boundary():
    contents = _read("app/services/stats_service.py")
    assert "StatsRepository" in contents
