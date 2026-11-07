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
