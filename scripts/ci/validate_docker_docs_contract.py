#!/usr/bin/env python3
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def contains_all(text: str, *terms: str) -> bool:
    lowered = text.lower()
    return all(term.lower() in lowered for term in terms)


def any_line_contains_all(text: str, *terms: str) -> bool:
    return any(contains_all(line, *terms) for line in text.splitlines())


compose = read("docker-compose.yml")
readme = read("README.md")
docker_guide = read("wiki/Docker.md")
deployment = read("docs/architecture/deployment.md")


checks = [
    (
        "docker-compose latest image alias",
        "image: pipepito/acestream-scraper:latest" in compose,
    ),
    (
        "docker-compose warp toggle",
        "- ENABLE_WARP=false" in compose,
    ),
    (
        "docker-compose acestream toggle",
        "- ENABLE_ACESTREAM_ENGINE=false" in compose,
    ),
    (
        "docker-compose acexy toggle",
        "- ENABLE_ACEXY=false" in compose,
    ),
    (
        "docker-compose zeronet sidecar",
        "zeronet:" in compose and "ZERONET_URL=http://host.docker.internal:43110" in compose,
    ),
    (
        "docker-compose zeronet profile",
        "profiles:" in compose and "- zeronet" in compose,
    ),
    (
        "docker-compose zeronet host gateway",
        "extra_hosts:" in compose and "host.docker.internal:host-gateway" in compose,
    ),
    (
        "docs explain latest full image",
        contains_all(readme, "latest", "scraper-acestream-acexy")
        and contains_all(docker_guide, "latest", "scraper-acestream-acexy")
        and contains_all(deployment, "latest", "scraper-acestream-acexy"),
    ),
    (
        "docs list explicit flavor tags",
        all(
            tag in readme and tag in docker_guide
            for tag in [
                "`scraper`",
                "`scraper-acestream`",
                "`scraper-acexy`",
                "`scraper-acestream-acexy`",
            ]
        ),
    ),
    (
        "docs explain warp install and enable flag",
        contains_all(readme, "warp", "every flavor", "enable_warp=true")
        and contains_all(docker_guide, "warp", "every flavor"),
    ),
    (
        "docs explain zeronet external contract",
        contains_all(readme, "zeronet", "external sidecar/service")
        and contains_all(docker_guide, "zeronet", "external sidecar/service")
        and contains_all(deployment, "zeronet", "external sidecar/service"),
    ),
    (
        "docs explain zeronet compose limitation",
        contains_all(readme, "zeronet", "amd64")
        and contains_all(docker_guide, "zeronet", "amd64")
        and contains_all(deployment, "zeronet", "amd64"),
    ),
    (
        "docs explain zeronet external default endpoint",
        contains_all(readme, "host.docker.internal", "43110")
        and contains_all(docker_guide, "host.docker.internal", "43110")
        and contains_all(deployment, "host.docker.internal", "43110"),
    ),
    (
        "docs avoid stale localhost zeronet default",
        all(
            stale_pattern not in text
            for text in [readme, docker_guide, deployment]
            for stale_pattern in [
                "`ZERONET_URL` (default: `http://127.0.0.1:43110`)",
                "`ZERONET_URL` (default: `http://localhost:43110`)",
            ]
        ),
    ),
    (
        "docs explain runtime env expectations",
        "ENABLE_ACESTREAM_ENGINE" in readme
        and "ENABLE_ACEXY" in readme
        and "ACESTREAM_HTTP_HOST" in docker_guide
        and "ACEXY_HOST" in docker_guide,
    ),
    (
        "docs explain manifest driven acestream availability",
        "docker/manifests/acestream.json" in readme
        and "docker/manifests/acestream.json" in docker_guide
        and "docker/manifests/acestream.json" in deployment,
    ),
    (
        "docs explain warp capabilities",
        "NET_ADMIN" in readme
        and "SYS_ADMIN" in readme
        and "NET_ADMIN" in docker_guide
        and "SYS_ADMIN" in docker_guide,
    ),
    (
        "docs explain acestream engine state volume",
        "/var/lib/acestream" in readme and "/var/lib/acestream" in docker_guide,
    ),
    (
        "readme marks arm/v7 acestream engine as experimental",
        any_line_contains_all(readme, "linux/arm/v7", "experimental"),
    ),
]


failed = [name for name, passed in checks if not passed]

if failed:
    for name in failed:
        print(f"FAIL: {name}")
    sys.exit(1)

for name, _ in checks:
    print(f"PASS: {name}")
