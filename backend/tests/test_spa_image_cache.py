"""Image timestamp normalization must not leave browsers on an old SPA shell."""
import os

import pytest


@pytest.mark.parametrize("path", ["/", "/settings"])
def test_spa_refreshes_with_identical_file_size_and_normalized_mtime(client, monkeypatch, tmp_path, path):
    import main

    monkeypatch.setattr(main, "frontend_dir", str(tmp_path))
    index = tmp_path / "index.html"
    index.write_text("<html>build-A</html>")
    os.utime(index, (946684800, 946684800))
    first = client.get(path)
    assert first.status_code == 200
    assert first.headers["cache-control"] == "no-store"

    index.write_text("<html>build-B</html>")
    os.utime(index, (946684800, 946684800))
    headers = {"If-Modified-Since": "Sat, 01 Jan 2000 00:00:00 GMT"}
    if "etag" in first.headers:
        headers["If-None-Match"] = first.headers["etag"]
    updated = client.get(path, headers=headers)
    assert updated.status_code == 200
    assert updated.headers["cache-control"] == "no-store"
    assert updated.text == "<html>build-B</html>"


@pytest.mark.parametrize("name,media_type,payload", [
    ("manifest.json", "application/manifest+json", b'{"name":"Acestream Scraper"}'),
    ("favicon.ico", "image/x-icon", b"\x00\x00\x01\x00"),
])
def test_root_assets_serve_their_bytes_and_never_spa_html(
    client, monkeypatch, tmp_path, name, media_type, payload,
):
    import main

    monkeypatch.setattr(main, "frontend_dir", str(tmp_path))
    (tmp_path / "index.html").write_text("<html>SPA</html>")
    asset = tmp_path / name
    asset.write_bytes(payload)
    response = client.get("/" + name)
    assert response.status_code == 200
    assert response.headers["content-type"] == media_type
    assert response.headers["cache-control"] == "no-cache"
    assert response.content == payload
    asset.unlink()
    missing = client.get("/" + name)
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Frontend asset not found"}
