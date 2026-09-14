#!/usr/bin/env python3
"""Sync Docker Hub overview text without building images or changing tags."""

import argparse
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler


ROOT = Path(__file__).resolve().parents[2]
API = "https://hub.docker.com"
REPOSITORY = "pipepito/acestream-scraper"


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, path, payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(API + path, data=json.dumps(payload).encode() if payload is not None else None,
                  headers=headers, method=method)
    try:
        with build_opener(NoRedirects()).open(req, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except HTTPError as exc:
        # Do not print response bodies, headers, or exceptions containing credentials.
        raise RuntimeError(f"Docker Hub {method} failed (HTTP {exc.code})") from None
    except (URLError, TimeoutError, ValueError):
        raise RuntimeError(f"Docker Hub {method} failed; check connectivity and API availability") from None


def publish(payload):
    username = os.environ.get("DOCKERHUB_USERNAME")
    secret = os.environ.get("DOCKERHUB_TOKEN")
    if not username or not secret:
        raise RuntimeError("DOCKERHUB_USERNAME and DOCKERHUB_TOKEN are required")
    auth = request("POST", "/v2/auth/token", {"identifier": username, "secret": secret})
    token = auth.get("access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("Docker Hub authentication returned no access token")
    endpoint = f"/v2/repositories/{REPOSITORY}/"
    current = request("GET", endpoint, token=token)
    if all(current.get(key) == value for key, value in payload.items()):
        print("Docker Hub description already up to date")
        return
    request("PATCH", endpoint, payload, token)
    updated = request("GET", endpoint, token=token)
    if any(updated.get(key) != value for key, value in payload.items()):
        raise RuntimeError("Docker Hub description verification failed; retry the description publish")
    print("Published and verified Docker Hub description")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    folder = ROOT / "docs/dockerhub"
    payload = {"description": (folder / "short-description.txt").read_text().strip(),
               "full_description": (folder / "README.md").read_text()}
    if not 0 < len(payload["description"]) <= 100 or not 0 < len(payload["full_description"]) <= 25000:
        raise RuntimeError("Docker Hub description is empty or exceeds its size limit")
    if args.dry_run:
        print(json.dumps({"repository": REPOSITORY, **payload}, indent=2))
    else:
        publish(payload)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
