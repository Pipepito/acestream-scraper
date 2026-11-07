# Media Integrations, Plan 1: Foundation and Engine Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the shared backend foundation every media feature depends on (settings/env contract, proxy trust, public base URL, LAN guard, engine client, byte relay, tuner network gate, stream ranking) plus the two engine fixes (amd64 `--bind-all` knob, startup schema upgrade for existing databases), all tested, without any user-visible feature yet except the fixed Playlist copy link.

**Architecture:** New small modules under `backend/app/` (`middleware/forwarded.py`, `services/public_url_service.py`, `services/engine_client.py`, `services/stream_relay.py`, `services/stream_ranking.py`, `services/tuner_network.py`, `api/endpoints/tuner.py`) wired through `main.py`/`api.py` following the existing `system.py` template; env knobs declared once in `Settings` and mirrored in `entrypoint.sh`. The relay and engine client are the byte path later plans reuse; `/tuner/stream/<id>.ts` ships now because remote players (plan 3) and tuners (plan 4) both hand it out.

**Tech Stack:** Python 3.12 (venv) / 3.13 (image), FastAPI + Starlette 1.0, httpx 0.28, SQLAlchemy 2, Alembic, pytest; React 18 + TS + react-query v5 + Jest for the small frontend slice.

**Spec:** `docs/superpowers/specs/2026-09-03-media-integrations-design.md` (sections 2, 4, 5.2 "Stream ranking", 9, 10). Read sections 4.1–4.6 before starting.

## Global Constraints

- Run backend tests from the repo root: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/<file>`. Use the `client` fixture (create_all) unless a test needs migration state, then `alembic_client`.
- Every new endpoint round-trips Pydantic DTOs with globally unique class names; after DTO changes run `backend/venv/bin/python backend/scripts/dump_openapi.py` then `cd frontend && npm run codegen` and commit `backend/openapi.json` + `frontend/src/types/api-generated.ts` (Task 13).
- HTTP 401 is reserved for the API token. Upstream/engine failures use `APIError` with 502 and a distinct code.
- Env knobs live in `app/config/settings.py` `Settings` and are read via `get_settings()`, never `os.environ` (exception: `API_TOKEN` and the existing flag helpers). `entrypoint.sh` exports the same names with byte-identical defaults.
- Blocking work never runs on the event loop: DB-touching handlers are sync `def`; relays are async and touch no DB.
- No `.js` files in `frontend/src`; named prop interfaces; no `any`; `npm run lint -- --max-warnings=0` and `npm run typecheck` must pass.
- Commit after each task with the trailer:
  `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01NCvyzQfF1uXiozTEGgDvPM`.
- Branch: `feature/media-integrations` (already checked out, off `develop`). Never commit `docs/superpowers/` (gitignored).

---

### Task 1: Settings fields for the new env knobs

**Files:**
- Modify: `backend/app/config/settings.py:85-121` (the `Settings` class)
- Test: `backend/tests/test_settings_env.py`

**Interfaces:**
- Produces: `Settings.PUBLIC_BASE_URL: str = ""`, `Settings.FORWARDED_ALLOW_IPS: str`, `Settings.TUNER_ALLOWED_NETWORKS: str`, `Settings.PLAYER_HLS_DIR: str`, `Settings.PLAYER_MAX_SESSIONS: int`, `Settings.PLAYER_START_TIMEOUT_SECONDS: int`, `Settings.FFMPEG_BINARY_PATH: str`, `Settings.MEDIA_SERVER_MIN_REFRESH_MINUTES: int` — read everywhere through `get_settings()`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_settings_env.py`:

```python
DEFAULT_TUNER_NETWORKS = "127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10"
DEFAULT_FORWARDED_ALLOW_IPS = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"


def test_media_integration_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "PUBLIC_BASE_URL", "FORWARDED_ALLOW_IPS", "TUNER_ALLOWED_NETWORKS", "PLAYER_HLS_DIR",
        "PLAYER_MAX_SESSIONS", "PLAYER_START_TIMEOUT_SECONDS", "FFMPEG_BINARY_PATH",
        "MEDIA_SERVER_MIN_REFRESH_MINUTES",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.PUBLIC_BASE_URL == ""
    assert settings.FORWARDED_ALLOW_IPS == DEFAULT_FORWARDED_ALLOW_IPS
    assert settings.TUNER_ALLOWED_NETWORKS == DEFAULT_TUNER_NETWORKS
    assert settings.PLAYER_HLS_DIR == "/tmp/acestream-player"
    assert settings.PLAYER_MAX_SESSIONS == 3
    assert settings.PLAYER_START_TIMEOUT_SECONDS == 45
    assert settings.FFMPEG_BINARY_PATH == ""
    assert settings.MEDIA_SERVER_MIN_REFRESH_MINUTES == 30


def test_media_integration_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://scraper.example.com")
    monkeypatch.setenv("PLAYER_MAX_SESSIONS", "5")
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
    settings = Settings(_env_file=None)
    assert settings.PUBLIC_BASE_URL == "https://scraper.example.com"
    assert settings.PLAYER_MAX_SESSIONS == 5
    assert settings.TUNER_ALLOWED_NETWORKS == "*"


def test_entrypoint_defaults_match_settings_defaults() -> None:
    """entrypoint.sh must export the same defaults Settings carries (spec 4.5)."""
    from pathlib import Path
    entrypoint = (Path(__file__).resolve().parents[2] / "entrypoint.sh").read_text(encoding="utf-8")
    assert 'export PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-}"' in entrypoint
    assert f'export TUNER_ALLOWED_NETWORKS="${{TUNER_ALLOWED_NETWORKS:-{DEFAULT_TUNER_NETWORKS}}}"' in entrypoint
    assert 'export PLAYER_HLS_DIR="${PLAYER_HLS_DIR:-/tmp/acestream-player}"' in entrypoint
    assert 'export PLAYER_MAX_SESSIONS="${PLAYER_MAX_SESSIONS:-3}"' in entrypoint
    assert f'export FORWARDED_ALLOW_IPS="${{FORWARDED_ALLOW_IPS:-{DEFAULT_FORWARDED_ALLOW_IPS}}}"' in entrypoint
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_settings_env.py`
Expected: FAIL (`AttributeError: 'Settings' object has no attribute 'PUBLIC_BASE_URL'`; the entrypoint assertion fails too — Task 2 fixes it).

- [ ] **Step 3: Add the fields**

In `backend/app/config/settings.py`, after `ACE_ENGINE_URL: str = "http://localhost:6878"` add:

```python
    # --- Media integrations (spec 4.3–4.5) ---------------------------------
    # Externally reachable origin (scheme://host[:port]) advertised to tuners,
    # remote players and the SPA copy link. Empty = derive from the request.
    PUBLIC_BASE_URL: str = ""
    # Peers whose X-Forwarded-* headers the app trusts (IPs, CIDRs, "*", or
    # literal tokens such as "testclient"). uvicorn's own proxy-header handling
    # is disabled in favour of app/middleware/forwarded.py.
    FORWARDED_ALLOW_IPS: str = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    # Networks allowed to reach the token-free /tuner/* routes ("*" disables).
    TUNER_ALLOWED_NETWORKS: str = (
        "127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10"
    )
    # Web player (plan 2).
    PLAYER_HLS_DIR: str = "/tmp/acestream-player"
    PLAYER_MAX_SESSIONS: int = 3
    PLAYER_START_TIMEOUT_SECONDS: int = 45
    FFMPEG_BINARY_PATH: str = ""
    # Media servers (plan 4): minimum minutes between automatic guide refreshes; 0 disables the debounce.
    MEDIA_SERVER_MIN_REFRESH_MINUTES: int = 30
```

- [ ] **Step 4: Run the tests again**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_settings_env.py`
Expected: the two `Settings` tests PASS; `test_entrypoint_defaults_match_settings_defaults` still FAILS until Task 2.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config/settings.py backend/tests/test_settings_env.py
git commit -m "feat(settings): declare media integration env knobs"
```

---

### Task 2: Runtime contract — entrypoint exports, uvicorn flags, compose, `ACESTREAM_BIND_ALL`

**Files:**
- Modify: `entrypoint.sh:225-246` (env export block), `entrypoint.sh:385-389` (engine launch), `entrypoint.sh:397-400` (APP_COMMAND), `entrypoint.sh:416` (trap order)
- Modify: `Dockerfile:306` (CMD), `Dockerfile:337-340` (scraper-acestream ENV)
- Modify: `docker/scripts/acestream-android/start-engine:56-62`
- Modify: `docker-compose.yml:8` (publish) and add `stop_grace_period`
- Modify: `backend/main.py:397-398` (`uvicorn.run`)
- Modify: `e2e/stack/backend-start.sh` (the `uvicorn` line — grep `uvicorn main:app`)
- Modify: `docs/ops/acestream-arm-engine.md:169`, `wiki/Docker.md:146`, `wiki/Configuration.md` (engine env table), `README.md` ("Docker Runtime Toggles")
- Test: `backend/tests/test_runtime_integration_guards.py`, `backend/tests/docker/test_acestream_runtime_smoke.py`

**Interfaces:**
- Produces: env `ACESTREAM_BIND_ALL` (default `true`) — entrypoint appends `--bind-all` to `ACESTREAM_START_COMMAND` when true and the command lacks it; uvicorn always runs with `--no-proxy-headers --timeout-graceful-shutdown 3`.

- [ ] **Step 1: Write the failing guard tests**

Append to `backend/tests/test_runtime_integration_guards.py`:

```python
def test_entrypoint_exports_media_integration_defaults():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()

    assert 'export PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-}"' in entrypoint
    assert (
        'export TUNER_ALLOWED_NETWORKS="${TUNER_ALLOWED_NETWORKS:-'
        '127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10}"'
    ) in entrypoint
    assert 'export PLAYER_HLS_DIR="${PLAYER_HLS_DIR:-/tmp/acestream-player}"' in entrypoint
    assert 'export PLAYER_MAX_SESSIONS="${PLAYER_MAX_SESSIONS:-3}"' in entrypoint
    assert 'export FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16}"' in entrypoint


def test_uvicorn_is_launched_with_app_owned_proxy_trust_and_graceful_timeout():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    e2e_start = (REPO_ROOT / "e2e" / "stack" / "backend-start.sh").read_text()

    flags = '--no-proxy-headers --timeout-graceful-shutdown 3'
    assert f'APP_COMMAND=(uvicorn main:app --host 0.0.0.0 --port "$FLASK_PORT" {flags})' in entrypoint
    assert 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers", "--timeout-graceful-shutdown", "3"]' in dockerfile
    assert "--no-proxy-headers" in e2e_start and "--timeout-graceful-shutdown 3" in e2e_start


def test_entrypoint_stops_the_app_before_sidecars_on_signals():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()
    # The lifespan's engine `stop` calls must reach a live engine, so the app
    # goes down first on INT/TERM (it already does on the normal exit path).
    assert """trap 'shutdown_children "$app_pid" "${child_pids[@]:-}"' INT TERM EXIT""" in entrypoint


def test_entrypoint_appends_bind_all_to_engine_command_by_default():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    start_engine = (REPO_ROOT / "docker" / "scripts" / "acestream-android" / "start-engine").read_text()

    assert 'ACESTREAM_BIND_ALL=$(normalize_bool "${ACESTREAM_BIND_ALL:-true}")' in entrypoint
    assert 'case " $ACESTREAM_START_COMMAND " in *" --bind-all "*) ;; *) ACESTREAM_START_COMMAND="$ACESTREAM_START_COMMAND --bind-all" ;; esac' in entrypoint
    assert "ACESTREAM_BIND_ALL=true" in dockerfile
    # The ARM launcher must not pass --bind-all twice or ignore the knob.
    assert 'if [ "$(printf \'%s\' "${ACESTREAM_BIND_ALL:-true}" | tr \'[:upper:]\' \'[:lower:]\')" != "false" ]; then' in start_engine
    assert '--bind-all' in start_engine


def test_docker_compose_publishes_ipv4_only_and_sets_stop_grace_period():
    compose_file = (REPO_ROOT / "docker-compose.yml").read_text()

    assert '- "0.0.0.0:8000:8000"' in compose_file
    assert "stop_grace_period: 20s" in compose_file
```

- [ ] **Step 2: Run the guard tests to verify they fail**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_runtime_integration_guards.py -k "media_integration or uvicorn_is_launched or stops_the_app or bind_all or ipv4_only"`
Expected: 5 FAIL.

- [ ] **Step 3: Edit `entrypoint.sh`**

After line 246 (`export IPFS_GATEWAY_URL=...`) add:

```bash
# Media integrations (spec 4.5): one declared default per knob, mirrored by
# app/config/settings.py. PUBLIC_BASE_URL is the origin tuners/players use to
# reach this container; TUNER_ALLOWED_NETWORKS gates the token-free /tuner/*
# routes; FORWARDED_ALLOW_IPS is consumed by the app's own forwarded-headers
# middleware (uvicorn's is disabled below).
export PUBLIC_BASE_URL="${PUBLIC_BASE_URL:-}"
export TUNER_ALLOWED_NETWORKS="${TUNER_ALLOWED_NETWORKS:-127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10}"
export PLAYER_HLS_DIR="${PLAYER_HLS_DIR:-/tmp/acestream-player}"
export PLAYER_MAX_SESSIONS="${PLAYER_MAX_SESSIONS:-3}"
export FORWARDED_ALLOW_IPS="${FORWARDED_ALLOW_IPS:-127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16}"
```

Replace the engine launch block (lines 385-389) with:

```bash
# The engine's HTTP API only admits loopback and RFC1918 clients by default;
# --bind-all lifts that so players on VPN/CGNAT ranges (Tailscale) or the
# Docker Desktop host path are accepted through a published 6878. The API is
# unauthenticated either way: publish 6878 only on trusted networks.
# ACESTREAM_BIND_ALL=false restores the engine's own address filter.
ACESTREAM_BIND_ALL=$(normalize_bool "${ACESTREAM_BIND_ALL:-true}")
export ACESTREAM_BIND_ALL
if feature_enabled "$ENABLE_ACESTREAM_ENGINE" && [ -n "${ACESTREAM_START_COMMAND:-}" ]; then
    if feature_enabled "$ACESTREAM_BIND_ALL"; then
        case " $ACESTREAM_START_COMMAND " in *" --bind-all "*) ;; *) ACESTREAM_START_COMMAND="$ACESTREAM_START_COMMAND --bind-all" ;; esac
    fi
    supervise_service "AceStream" "$ACESTREAM_START_COMMAND" &
    child_pids+=("$!")
    child_names+=("AceStream")
fi
```

Replace the APP_COMMAND default (line 399) with:

```bash
    # --no-proxy-headers: the app's ForwardedHeadersMiddleware owns X-Forwarded-*
    # trust (FORWARDED_ALLOW_IPS). --timeout-graceful-shutdown: live stream
    # relays would otherwise hold the shutdown open until Docker's SIGKILL.
    APP_COMMAND=(uvicorn main:app --host 0.0.0.0 --port "$FLASK_PORT" --no-proxy-headers --timeout-graceful-shutdown 3)
```

Replace the trap (line 416) with:

```bash
trap 'shutdown_children "$app_pid" "${child_pids[@]:-}"' INT TERM EXIT
```

- [ ] **Step 4: Edit `Dockerfile`, `start-engine`, `docker-compose.yml`, `main.py`, `e2e/stack/backend-start.sh`**

`Dockerfile:306`:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers", "--timeout-graceful-shutdown", "3"]
```

`Dockerfile:337-340` (scraper-acestream stage ENV) — add the knob:

```dockerfile
ENV IMAGE_HAS_ACESTREAM=true \
    ACESTREAM_BINARY_PATH=/opt/acestream/bin/acestreamengine \
    ACESTREAM_HOME=/var/lib/acestream \
    ACESTREAM_BIND_ALL=true \
    ACESTREAM_START_COMMAND="env PYTHONPATH=/opt/acestream/python-deps /opt/acestream/start-engine --client-console --http-port 6878"
```

`docker/scripts/acestream-android/start-engine` — replace the final `exec` block (from `cd "$ACE"` to the end) with:

```sh
cd "$ACE"
# --bind-all unless ACESTREAM_BIND_ALL=false (the entrypoint appends it to the
# start command too; never pass it twice).
if [ "$(printf '%s' "${ACESTREAM_BIND_ALL:-true}" | tr '[:upper:]' '[:lower:]')" != "false" ]; then
    case " $* " in *" --bind-all "*) ;; *) set -- --bind-all "$@" ;; esac
fi
exec "$ACE/python/bin/python" "$ACE/main_linux.py" \
    --http-port "${ACESTREAM_HTTP_PORT:-6878}" \
    --disable-sentry \
    --log-stdout \
    "$@"
```

Also update the script's header comment: replace the two lines starting `# --bind-all lets the engine accept` … `# authentication.` with:

```sh
# --bind-all is added unless ACESTREAM_BIND_ALL=false so clients arriving
# through a published 6878 port are accepted (the engine otherwise admits only
# loopback and RFC1918 sources). The engine API has no authentication: publish
# 6878 only on trusted networks.
```

`docker-compose.yml` — change the `ports:` entry and add the grace period under `app:`:

```yaml
    ports:
      # IPv4-only on purpose: an unaddressed "8000:8000" also listens on [::]
      # and docker-proxy rewrites every IPv6 client to the bridge gateway,
      # which defeats TUNER_ALLOWED_NETWORKS. For IPv6, enable it on the network
      # and add "[::]:8000:8000".
      - "0.0.0.0:8000:8000"
```

and after `image: pipepito/acestream-scraper:latest`:

```yaml
    # Live stream relays get 3 s to close, then the app tears down ffmpeg and
    # engine sessions; give Docker enough room before its SIGKILL.
    stop_grace_period: 20s
```

`backend/main.py:398`:

```python
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, proxy_headers=False, timeout_graceful_shutdown=3)
```

`e2e/stack/backend-start.sh` — append ` --no-proxy-headers --timeout-graceful-shutdown 3` to the `uvicorn main:app` invocation (keep everything else on that line).

- [ ] **Step 5: Docs**

`docs/ops/acestream-arm-engine.md:169` — replace the bullet with:

```markdown
- The engine is started with `--bind-all` (env `ACESTREAM_BIND_ALL`, default `true`, on every platform) so clients arriving through a published `6878` port are accepted whatever their address; without it the engine only admits loopback and RFC1918 sources and answers `Internal server error` to VPN/CGNAT (Tailscale) or Docker Desktop host clients. The engine API is unauthenticated: publish `6878` only on trusted networks, or set `ACESTREAM_BIND_ALL=false` to keep the engine's own address filter.
```

`wiki/Docker.md:146` — replace `the ARM engine is started with `--bind-all` so published-port clients are accepted` with `the engine is started with `--bind-all` on every platform (`ACESTREAM_BIND_ALL=true` by default; set it to `false` to keep the engine's loopback/RFC1918-only filter) so published-port clients are accepted`.

`wiki/Configuration.md` — in the Acestream env table add a row:

```markdown
| `ACESTREAM_BIND_ALL` | `true` | Append `--bind-all` to the engine start command so any client address is accepted on a published `6878` (the engine otherwise admits only loopback/RFC1918 sources). `false` restores the engine's own filter. |
```

`README.md` "Docker Runtime Toggles" — add `ACESTREAM_BIND_ALL` (default `true`) with the one-line description above, next to `ENABLE_ACESTREAM_ENGINE`.

- [ ] **Step 6: Extend the docker smoke test (runs only with a Docker daemon)**

In `backend/tests/docker/test_acestream_runtime_smoke.py`, inside the `try:` block after the `status` assertion, add:

```python
        # A client from a non-RFC1918 range must be admitted now that the
        # entrypoint passes --bind-all (spec: ACESTREAM_BIND_ALL default true).
        network = f"acestream-smoke-net-{host_port}"
        subprocess.run(["docker", "network", "rm", network], capture_output=True)
        subprocess.run(
            ["docker", "network", "create", "--subnet", "11.22.33.0/24", network],
            check=True, capture_output=True,
        )
        try:
            subprocess.run(["docker", "network", "connect", network, container], check=True, capture_output=True)
            engine_ip = subprocess.run(
                ["docker", "inspect", "-f",
                 "{{(index .NetworkSettings.Networks \"" + network + "\").IPAddress}}", container],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            probe = subprocess.run(
                ["docker", "run", "--rm", "--network", network, "--ip", "11.22.33.4",
                 "curlimages/curl:8.10.1", "-fsS", "--max-time", "15",
                 f"http://{engine_ip}:6878/webui/api/service?method=get_version"],
                capture_output=True, text=True, timeout=60,
            )
            assert probe.returncode == 0, (
                f"engine denied a non-RFC1918 client (11.22.33.4) on {platform}: {probe.stderr!r}"
            )
        finally:
            subprocess.run(["docker", "network", "disconnect", "-f", network, container], capture_output=True)
            subprocess.run(["docker", "network", "rm", network], capture_output=True)
```

- [ ] **Step 7: Run the guards and the settings test**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_runtime_integration_guards.py backend/tests/test_settings_env.py`
Expected: PASS. Also run `bash scripts/ci/validate_command_builder.sh` (must still pass: the tuple is unchanged in this plan) and `docker compose config >/dev/null`.

- [ ] **Step 8: Commit**

```bash
git add entrypoint.sh Dockerfile docker/scripts/acestream-android/start-engine docker-compose.yml backend/main.py e2e/stack/backend-start.sh docs/ops/acestream-arm-engine.md wiki/Docker.md wiki/Configuration.md README.md backend/tests/test_runtime_integration_guards.py backend/tests/docker/test_acestream_runtime_smoke.py
git commit -m "feat(runtime): media env contract, app-owned proxy trust flags, ACESTREAM_BIND_ALL knob"
```

---

### Task 3: Startup schema upgrade for existing databases (with backup)

**Files:**
- Modify: `backend/app/config/database.py:164-197`
- Modify: `backend/main.py:55-86`
- Test: `backend/tests/test_startup_db_init.py`
- Modify: `CLAUDE.md` (startup sequence bullet 2, second sub-bullet)

**Interfaces:**
- Produces: `database.current_revision(database_url=None) -> Optional[str]`, `database.head_revision() -> str`, `database.backup_sqlite(database_url, label) -> Optional[str]` (path of the copy), and `provision_schema()` called unconditionally by `initialize_database()`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_startup_db_init.py`:

```python
def test_startup_upgrades_existing_stamped_database_with_backup(tmp_path):
    """Existing installs must receive new revisions: startup upgrades a
    database stamped behind head and keeps a pre-upgrade copy."""
    from tests.migration_test_utils import upgrade_to_revision

    db_path = tmp_path / "config" / "scraper.db"
    db_path.parent.mkdir(parents=True)
    legacy_db_path = tmp_path / "config" / "acestream.db"
    upgrade_to_revision(db_path, "20260824_1000")
    assert "base_urls" not in _inspect_tables(db_path)

    result = _run_main_import(
        database_url=_database_url_for(db_path),
        legacy_database_url=_database_url_for(legacy_db_path),
        frontend_build_path=tmp_path / "frontend-build",
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "base_urls" in _inspect_tables(db_path)
    assert "Upgrading v2 database schema 20260824_1000 ->" in result.stdout
    backups = list((tmp_path / "config" / "backups").glob("*-pre-upgrade-20260824_1000-*/scraper.db"))
    assert len(backups) == 1, result.stdout
    # The copy is the pre-upgrade schema.
    assert "base_urls" not in _inspect_tables(backups[0])


def test_startup_at_head_writes_no_backup(tmp_path):
    from tests.migration_test_utils import upgrade_to_head

    db_path = tmp_path / "config" / "scraper.db"
    db_path.parent.mkdir(parents=True)
    legacy_db_path = tmp_path / "config" / "acestream.db"
    upgrade_to_head(db_path)

    result = _run_main_import(
        database_url=_database_url_for(db_path),
        legacy_database_url=_database_url_for(legacy_db_path),
        frontend_build_path=tmp_path / "frontend-build",
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert not (tmp_path / "config" / "backups").exists()
    assert "V2 database ready" in result.stdout
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_startup_db_init.py -k "stamped_database_with_backup or at_head_writes_no_backup"`
Expected: the first FAILS (`base_urls` missing, no backup); the second PASSES already (keep it as a regression guard).

- [ ] **Step 3: Add the helpers to `database.py`**

Append to `backend/app/config/database.py`:

```python
def current_revision(database_url: Optional[str] = None) -> Optional[str]:
    """The revision recorded in ``alembic_version`` (None when unstamped/missing)."""
    import os
    import sqlite3

    url = database_url or get_settings().DATABASE_URL
    path = _sqlite_path_from_url(url)
    if path is None or not os.path.exists(path):
        return None
    conn = sqlite3.connect(path)
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "alembic_version" not in names:
            return None
        row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def head_revision() -> str:
    """The Alembic head of the bundled migrations."""
    from alembic.script import ScriptDirectory

    return ScriptDirectory.from_config(_alembic_config()).get_current_head()


def backup_sqlite(database_url: Optional[str] = None, label: str = "pre-upgrade") -> Optional[str]:
    """Copy the SQLite file to ``<db dir>/backups/<stamp>-<label>/<name>`` via the
    online backup API (safe while the file is open). Returns the copy's path, or
    None for non-SQLite URLs."""
    import os
    import sqlite3
    from datetime import datetime, timezone

    url = database_url or get_settings().DATABASE_URL
    path = _sqlite_path_from_url(url)
    if path is None or not os.path.exists(path):
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    target_dir = os.path.join(os.path.dirname(os.path.abspath(path)), "backups", f"{stamp}-{label}")
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, os.path.basename(path))
    source = sqlite3.connect(path)
    try:
        destination = sqlite3.connect(target)
        try:
            source.backup(destination)
        finally:
            destination.close()
    finally:
        source.close()
    return target
```

- [ ] **Step 4: Make `initialize_database()` converge every database**

Replace lines 74-85 of `backend/main.py` with:

```python
    # Every database converges to the Alembic head on startup (spec 4.6):
    # fresh files are provisioned, unstamped ones (pre-2026-08-29 migrator)
    # are stamped first, and existing databases receive new revisions. A
    # pending upgrade is preceded by an on-disk copy under <db dir>/backups/.
    current = current_revision()
    target = head_revision()
    if os.path.exists(migrator.v2_db_path) and current != target:
        backup_path = backup_sqlite(label=f"pre-upgrade-{current or 'unstamped'}-{target}")
        print(f"Upgrading v2 database schema {current or 'unstamped'} -> {target} (backup: {backup_path})")
    state = provision_schema()
    if state == "missing":
        print("Fresh v2 database created via Alembic!")
    elif state == "unstamped":
        print("Recorded the current Alembic head on the existing (unstamped) v2 database")
    print("V2 database ready")
```

and change the import on line 26 to:

```python
from app.config.database import backup_sqlite, current_revision, get_db, head_revision, provision_schema
```

(`ensure_schema_stamped` is no longer imported by `main.py`; it is still used by `provision_schema`.) `test_startup_stamps_existing_unstamped_v2_database` asserts `"unstamped" in result.stdout` — the messages above keep that word.

- [ ] **Step 5: Run the startup tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_startup_db_init.py backend/tests/test_migrate_database.py`
Expected: PASS (the fresh-db and v1 tests keep passing; the message "Creating fresh v2 database via Alembic..." was replaced — grep the tests for it first: `grep -rn "fresh v2 database" backend/tests` and update any assertion to the new text).

- [ ] **Step 6: Update CLAUDE.md**

In the "Backend startup sequence" bullet 2, replace the sentence `Otherwise, if the v2 db file is missing, it provisions the schema via provision_schema() (Alembic upgrade head, same path as tests/deployments). Existing v2 dbs are left alone, except that a db with application tables but no alembic_version (…) is stamped with the current head (ensure_schema_stamped) so later revisions apply.` with:

`Then it always calls provision_schema(): a missing file is provisioned, a db with application tables but no alembic_version (what the pre-2026-08-29 migrator's create_all left behind) is stamped with the head first, and an existing stamped db is upgraded to head. When the recorded revision differs from the head, startup first copies the SQLite file to <db dir>/backups/<UTC stamp>-pre-upgrade-<from>-<to>/scraper.db (sqlite3 online backup) and logs one "Upgrading v2 database schema" line. An upgrade failure aborts startup; there is no create_all fallback.`

- [ ] **Step 7: Commit**

```bash
git add backend/app/config/database.py backend/main.py backend/tests/test_startup_db_init.py CLAUDE.md
git commit -m "fix(startup): upgrade existing databases to the Alembic head with a pre-upgrade backup"
```

---

### Task 4: Forwarded-headers middleware (app-owned proxy trust)

**Files:**
- Create: `backend/app/middleware/__init__.py` (empty), `backend/app/middleware/forwarded.py`
- Modify: `backend/main.py` (register after CORS)
- Test: `backend/tests/test_forwarded_middleware.py`

**Interfaces:**
- Produces: `parse_trusted(spec: str) -> TrustedPeers` with `TrustedPeers.contains(host: str) -> bool`; `ForwardedHeadersMiddleware(app, trusted: TrustedPeers)`; after it runs, `request.state.peer == (host, port)` (raw), `request.state.forwarded: bool`, and `request.client`/`request.url` are the corrected values. Later tasks read `request.state.peer` and `request.client.host`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_forwarded_middleware.py`:

```python
"""ForwardedHeadersMiddleware: the app, not uvicorn, decides which peers'
X-Forwarded-* headers to trust (spec 4.3)."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted


def _app(trusted: str) -> TestClient:
    app = FastAPI()

    @app.get("/probe")
    async def probe(request: Request):
        return {
            "scheme": request.url.scheme,
            "host": request.url.netloc,
            "client": request.client.host if request.client else None,
            "peer": list(request.state.peer),
            "forwarded": request.state.forwarded,
        }

    app.add_middleware(ForwardedHeadersMiddleware, trusted=parse_trusted(trusted))
    return TestClient(app)


FORWARDED = {
    "X-Forwarded-Proto": "https",
    "X-Forwarded-Host": "scraper.example.com",
    "X-Forwarded-For": "203.0.113.7",
}


def test_trusted_peer_headers_rewrite_scheme_host_and_client():
    body = _app("testclient").get("/probe", headers=FORWARDED).json()
    assert body["scheme"] == "https"
    assert body["host"] == "scraper.example.com"
    assert body["client"] == "203.0.113.7"
    assert body["peer"] == ["testclient", 50000]
    assert body["forwarded"] is True


def test_untrusted_peer_headers_are_ignored():
    body = _app("10.0.0.0/8").get("/probe", headers=FORWARDED).json()
    assert body["scheme"] == "http"
    assert body["host"] == "testserver"
    assert body["client"] == "testclient"
    assert body["forwarded"] is False


def test_rightmost_untrusted_hop_wins_and_all_trusted_keeps_raw_peer():
    client = _app("testclient,10.0.0.0/8")
    body = client.get("/probe", headers={"X-Forwarded-For": "198.51.100.9, 10.1.1.1"}).json()
    assert body["client"] == "198.51.100.9"
    body = client.get("/probe", headers={"X-Forwarded-For": "10.1.1.1, 10.2.2.2"}).json()
    assert body["client"] == "testclient"


def test_invalid_proto_is_ignored():
    body = _app("testclient").get("/probe", headers={"X-Forwarded-Proto": "gopher"}).json()
    assert body["scheme"] == "http"


def test_wildcard_trusts_everyone():
    body = _app("*").get("/probe", headers=FORWARDED).json()
    assert body["forwarded"] is True


@pytest.mark.parametrize(
    ("spec", "host", "expected"),
    [
        ("127.0.0.1", "127.0.0.1", True),
        ("10.0.0.0/8", "10.20.30.40", True),
        ("10.0.0.0/8", "192.168.1.1", False),
        ("testclient", "testclient", True),
        ("::1/128", "::1", True),
        ("192.168.0.0/16", "::ffff:192.168.1.5", True),
        ("bogus/99, 10.0.0.0/8", "10.0.0.1", True),
        ("", "10.0.0.1", False),
    ],
)
def test_parse_trusted(spec, host, expected):
    assert parse_trusted(spec).contains(host) is expected
```

- [ ] **Step 2: Run them to verify they fail**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_forwarded_middleware.py`
Expected: FAIL with `ModuleNotFoundError: app.middleware`.

- [ ] **Step 3: Implement the middleware**

Create `backend/app/middleware/__init__.py` (empty) and `backend/app/middleware/forwarded.py`:

```python
"""Pure-ASGI forwarded-headers middleware (spec 4.3).

The app owns proxy trust: when the raw peer is in FORWARDED_ALLOW_IPS the
X-Forwarded-Proto / X-Forwarded-Host / X-Forwarded-For headers rewrite the
scope once. uvicorn is started with --no-proxy-headers so nothing else
touches these values. The raw peer is always kept in scope["state"]["peer"].
"""
from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

_ALLOWED_PROTOS = {"http", "https", "ws", "wss"}


def _canonical(host: str) -> Optional[ipaddress._BaseAddress]:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return None
    mapped = getattr(address, "ipv4_mapped", None)
    return mapped if mapped is not None else address


@dataclass
class TrustedPeers:
    networks: List[ipaddress._BaseNetwork] = field(default_factory=list)
    literals: Set[str] = field(default_factory=set)
    everyone: bool = False

    def contains(self, host: Optional[str]) -> bool:
        if not host:
            return False
        if self.everyone:
            return True
        if host in self.literals:
            return True
        address = _canonical(host)
        if address is None:
            return False
        return any(address in network for network in self.networks)


def parse_trusted(spec: str) -> TrustedPeers:
    """Parse a comma-separated list of IPs, CIDRs, '*' or literal peer names."""
    trusted = TrustedPeers()
    for raw in (spec or "").split(","):
        token = raw.strip()
        if not token:
            continue
        if token == "*":
            trusted.everyone = True
            continue
        try:
            trusted.networks.append(ipaddress.ip_network(token, strict=False))
            continue
        except ValueError:
            pass
        if "/" in token:
            logger.warning("Ignoring malformed trusted network %r", token)
            continue
        trusted.literals.add(token)
    return trusted


def _header(scope, name: bytes) -> Optional[str]:
    for key, value in scope.get("headers", ()):
        if key.lower() == name:
            return value.decode("latin-1")
    return None


def _set_header(scope, name: bytes, value: str) -> None:
    headers = [(k, v) for k, v in scope.get("headers", ()) if k.lower() != name]
    headers.append((name, value.encode("latin-1")))
    scope["headers"] = headers


def _client_from_forwarded_for(value: str, trusted: TrustedPeers, raw_host: str) -> str:
    hops = [hop.strip() for hop in value.split(",") if hop.strip()]
    for hop in reversed(hops):
        if not trusted.contains(hop):
            return hop
    # Every hop is a trusted proxy: keep the raw peer rather than the first
    # entry (which the client itself may have forged).
    return raw_host


class ForwardedHeadersMiddleware:
    def __init__(self, app, trusted: TrustedPeers):
        self.app = app
        self.trusted = trusted

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        client = scope.get("client") or (None, 0)
        raw_host = client[0]
        state = scope.setdefault("state", {})
        state["peer"] = (raw_host, client[1] if len(client) > 1 else 0)
        state["forwarded"] = False

        if self.trusted.contains(raw_host):
            proto = _header(scope, b"x-forwarded-proto")
            if proto:
                proto = proto.split(",")[0].strip().lower()
                if proto in _ALLOWED_PROTOS:
                    scope["scheme"] = proto if scope["type"] == "http" else proto.replace("http", "ws")
                    state["forwarded"] = True
            forwarded_host = _header(scope, b"x-forwarded-host")
            if forwarded_host:
                _set_header(scope, b"host", forwarded_host.split(",")[0].strip())
                state["forwarded"] = True
            forwarded_for = _header(scope, b"x-forwarded-for")
            if forwarded_for:
                scope["client"] = (_client_from_forwarded_for(forwarded_for, self.trusted, raw_host), 0)
                state["forwarded"] = True
        await self.app(scope, receive, send)
```

- [ ] **Step 4: Register it in `main.py`**

After the CORS `app.add_middleware(...)` block add:

```python
# Outermost user middleware: rewrites scheme/host/client from X-Forwarded-*
# only for peers in FORWARDED_ALLOW_IPS and records the raw peer as
# request.state.peer (spec 4.3). uvicorn runs with --no-proxy-headers.
from app.config.settings import get_settings
from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted
app.add_middleware(ForwardedHeadersMiddleware, trusted=parse_trusted(get_settings().FORWARDED_ALLOW_IPS))
```

- [ ] **Step 5: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_forwarded_middleware.py backend/tests/test_error_contracts.py backend/tests/test_api_token_auth.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/middleware backend/main.py backend/tests/test_forwarded_middleware.py
git commit -m "feat(http): app-owned forwarded-headers middleware"
```

---

### Task 5: Public base URL (setting, resolver, endpoints)

**Files:**
- Modify: `backend/app/repositories/settings_repository.py`
- Modify: `backend/app/services/config_service.py`
- Modify: `backend/app/schemas/config.py`, `backend/app/api/endpoints/config.py`
- Create: `backend/app/services/public_url_service.py`
- Modify: `backend/app/schemas/system.py`, `backend/app/api/endpoints/system.py`
- Test: `backend/tests/test_public_url.py`, `backend/tests/test_config.py`

**Interfaces:**
- Produces: `SettingsRepository.PUBLIC_BASE_URL = "public_base_url"`; `ConfigService.get_public_base_url() -> str`, `ConfigService.set_public_base_url(value: str) -> bool` (422 on invalid); `public_url_service.resolve_public_base_url(request: Request, settings_repo: SettingsRepository) -> ResolvedPublicUrl(url: str, source: Literal["setting","forwarded","request"], warnings: list[str])`; `GET /api/v1/system/public-url -> PublicUrlResponse{url, source, warnings}`; `PUT /api/v1/config/public_base_url {value}`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_public_url.py`:

```python
"""Public base URL resolution (spec 4.3)."""
import pytest
from fastapi import status

from app.config.settings import get_settings


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_request_derived_url_when_unset(alembic_client, clean_env):
    body = alembic_client.get("/api/v1/system/public-url").json()
    assert body == {"url": "http://testserver", "source": "request", "warnings": ["unset"]}


def test_setting_wins_and_strips_slash(alembic_client, clean_env):
    put = alembic_client.put("/api/v1/config/public_base_url", json={"value": "https://scraper.example.com/"})
    assert put.status_code == status.HTTP_200_OK
    assert put.json()["value"] == "https://scraper.example.com"
    body = alembic_client.get("/api/v1/system/public-url").json()
    assert body["url"] == "https://scraper.example.com"
    assert body["source"] == "setting"
    assert body["warnings"] == ["proxied"]  # setting host differs from the request host


def test_forwarded_headers_change_source(alembic_client, clean_env, monkeypatch):
    # The test client peer is "testclient"; trust it for this test.
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "testclient")
    get_settings.cache_clear()
    import main
    from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted
    # Rebuild the middleware stack with the new trust list (add_middleware is import-time).
    for layer in main.app.user_middleware:
        if layer.cls is ForwardedHeadersMiddleware:
            layer.kwargs["trusted"] = parse_trusted("testclient")
    main.app.middleware_stack = None  # force rebuild
    body = alembic_client.get(
        "/api/v1/system/public-url",
        headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "scraper.example.com"},
    ).json()
    assert body["url"] == "https://scraper.example.com"
    assert body["source"] == "forwarded"
    assert body["warnings"] == ["unset"]
    for layer in main.app.user_middleware:
        if layer.cls is ForwardedHeadersMiddleware:
            layer.kwargs["trusted"] = parse_trusted(get_settings().FORWARDED_ALLOW_IPS)
    main.app.middleware_stack = None


@pytest.mark.parametrize("value", ["http://localhost:8000", "http://127.0.0.1:8000", "http://172.17.0.2:8000", "http://192.168.65.1:8000"])
def test_warnings_for_unreachable_hosts(alembic_client, clean_env, value):
    alembic_client.put("/api/v1/config/public_base_url", json={"value": value})
    body = alembic_client.get("/api/v1/system/public-url").json()
    expected = "localhost" if "localhost" in value or "127.0.0.1" in value else "docker-internal"
    assert expected in body["warnings"]


@pytest.mark.parametrize("bad", ["scraper.example.com", "ftp://x", "http://host/path", "http://host?x=1", "http://user:pw@host"])
def test_invalid_public_base_url_is_422(alembic_client, clean_env, bad):
    response = alembic_client.put("/api/v1/config/public_base_url", json={"value": bad})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_empty_value_clears_the_override(alembic_client, clean_env):
    alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://scraper.lan:8000"})
    response = alembic_client.put("/api/v1/config/public_base_url", json={"value": ""})
    assert response.status_code == status.HTTP_200_OK
    assert alembic_client.get("/api/v1/system/public-url").json()["source"] == "request"


def test_env_seeds_the_setting(alembic_client, monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://seeded.lan:8000")
    get_settings.cache_clear()
    try:
        body = alembic_client.get("/api/v1/config/public_base_url").json()
        assert body == {"key": "public_base_url", "value": "http://seeded.lan:8000"}
    finally:
        get_settings.cache_clear()


def test_generic_key_routes_serve_public_base_url(alembic_client, clean_env):
    assert alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://a.lan"}).status_code == 200
    assert alembic_client.get("/api/v1/config/public_base_url").json()["value"] == "http://a.lan"
```

Note on `test_env_seeds_the_setting`: `alembic_client` provisions a fresh database per test and `ConfigService.__init__` runs `setup_defaults()` on first use, so the seed happens on the first request of this test.

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_public_url.py`
Expected: FAIL (404s).

- [ ] **Step 3: Settings repository key and property default**

In `backend/app/repositories/settings_repository.py` add after `ACESTREAM_CHECK_TIMEOUT = 'acestream_check_timeout'`:

```python
    PUBLIC_BASE_URL = 'public_base_url'
```

and after `DEFAULT_ACESTREAM_CHECK_TIMEOUT = '10'`:

```python
    @property
    def DEFAULT_PUBLIC_BASE_URL(self) -> str:  # noqa: N802 - matches the DEFAULT_<KEY> lookup convention
        # Read at call time (not import time) so tests and runtime env changes apply.
        from app.config.settings import get_settings
        return get_settings().PUBLIC_BASE_URL or ''
```

and in `setup_defaults()` add the entry:

```python
            self.PUBLIC_BASE_URL: (self.DEFAULT_PUBLIC_BASE_URL, "Externally reachable origin for tuners and players"),
```

- [ ] **Step 4: ConfigService validation**

In `backend/app/services/config_service.py` add after `set_ace_engine_url`:

```python
    @staticmethod
    def normalize_public_base_url(value: str) -> str:
        """Accept http(s)://host[:port] only; strip a trailing slash; '' clears."""
        from urllib.parse import urlsplit

        candidate = (value or "").strip()
        if not candidate:
            return ""
        parts = urlsplit(candidate)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise HTTPException(status_code=422, detail="public_base_url must be http(s)://host[:port]")
        if parts.path not in ("", "/") or parts.query or parts.fragment or parts.username or parts.password:
            raise HTTPException(status_code=422, detail="public_base_url must not contain a path, query, fragment or credentials")
        return f"{parts.scheme}://{parts.netloc}"

    def get_public_base_url(self) -> str:
        return self.settings_repo.get_setting(SettingsRepository.PUBLIC_BASE_URL) or ""

    def set_public_base_url(self, value: str) -> bool:
        normalized = self.normalize_public_base_url(value)
        return self.settings_repo.set_setting(
            SettingsRepository.PUBLIC_BASE_URL,
            normalized,
            "Externally reachable origin for tuners and players",
        )
```

- [ ] **Step 5: Config endpoints and DTO**

In `backend/app/schemas/config.py` add:

```python
class PublicBaseUrlUpdate(BaseModel):
    """Schema for updating the externally reachable origin (spec 4.3)."""
    value: str = Field("", description="http(s)://host[:port]; empty clears the override")
```

In `backend/app/api/endpoints/config.py`: import `PublicBaseUrlUpdate`; add dedicated routes before `@router.get("/all", ...)`:

```python
@router.get("/public_base_url", response_model=SettingResponse)
def get_public_base_url(config_service: ConfigService = Depends(get_config_service)):
    """Externally reachable origin used for tuner, player and copy links."""
    return {"key": "public_base_url", "value": config_service.get_public_base_url()}


@router.put("/public_base_url", response_model=ConfigUpdateResponse)
def update_public_base_url(
    update: PublicBaseUrlUpdate,
    config_service: ConfigService = Depends(get_config_service),
):
    success = config_service.set_public_base_url(update.value)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update public_base_url")
    return {"message": "Setting updated successfully", "value": config_service.get_public_base_url()}
```

In `get_config_key` add before the `else`:

```python
    elif key == "public_base_url":
        value = config_service.get_public_base_url()
```

In `update_config_key` add before the final `raise HTTPException(404)`:

```python
    if key == "public_base_url":
        success = config_service.set_public_base_url(value or "")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update public_base_url")
        return {"message": "Setting updated successfully", "value": config_service.get_public_base_url()}
```

- [ ] **Step 6: Resolver service and system endpoint**

Create `backend/app/services/public_url_service.py`:

```python
"""Resolve the origin external clients (tuners, players, copied links) must use (spec 4.3)."""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import List, Literal
from urllib.parse import urlsplit

from fastapi import Request

from app.repositories.settings_repository import SettingsRepository

PublicUrlSource = Literal["setting", "forwarded", "request"]

_DOCKER_DESKTOP_GATEWAY = ipaddress.ip_network("192.168.65.0/24")
_DOCKER_BRIDGE = ipaddress.ip_network("172.16.0.0/12")


@dataclass
class ResolvedPublicUrl:
    url: str
    source: PublicUrlSource
    warnings: List[str] = field(default_factory=list)


def _host_warnings(url: str) -> List[str]:
    host = urlsplit(url).hostname or ""
    if host in ("localhost", "0.0.0.0", "::", "::1") or host.startswith("127."):
        return ["localhost"]
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return []
    if address in _DOCKER_DESKTOP_GATEWAY or address in _DOCKER_BRIDGE:
        return ["docker-internal"]
    return []


def request_origin(request: Request) -> str:
    """scheme://netloc of the (already forwarded-corrected) request."""
    return f"{request.url.scheme}://{request.url.netloc}"


def resolve_public_base_url(request: Request, settings_repo: SettingsRepository) -> ResolvedPublicUrl:
    configured = (settings_repo.get_setting(SettingsRepository.PUBLIC_BASE_URL) or "").strip()
    if configured:
        warnings = _host_warnings(configured)
        if urlsplit(configured).hostname != request.url.hostname:
            warnings.append("proxied")
        return ResolvedPublicUrl(url=configured.rstrip("/"), source="setting", warnings=warnings)
    origin = request_origin(request)
    forwarded = bool(getattr(request.state, "forwarded", False))
    warnings = _host_warnings(origin) + ["unset"]
    return ResolvedPublicUrl(url=origin, source="forwarded" if forwarded else "request", warnings=warnings)
```

In `backend/app/schemas/system.py` add:

```python
class PublicUrlResponse(BaseModel):
    """The origin external clients must use to reach this server (spec 4.3)."""
    url: str = Field(description="scheme://host[:port], no trailing slash")
    source: Literal["setting", "forwarded", "request"]
    warnings: List[str] = Field(default_factory=list, description="localhost | docker-internal | unset | proxied")
```

In `backend/app/api/endpoints/system.py` import `Request`, `PublicUrlResponse`, `resolve_public_base_url` and add:

```python
@router.get("/public-url", response_model=PublicUrlResponse, summary="Origin external clients must use")
def get_public_url(request: Request, db: Session = Depends(get_db)):
    resolved = resolve_public_base_url(request, SettingsRepository(db))
    return PublicUrlResponse(url=resolved.url, source=resolved.source, warnings=resolved.warnings)
```

- [ ] **Step 7: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_public_url.py backend/tests/test_config.py backend/tests/contracts/test_config_contracts.py`
Expected: PASS. `test_config_contracts.py` may pin `/config/all` keys — `get_all_settings()` is unchanged (the new key appears only once seeded; check the contract test tolerates extra keys, it asserts presence not exact equality).

- [ ] **Step 8: Commit**

```bash
git add backend/app/repositories/settings_repository.py backend/app/services/config_service.py backend/app/schemas/config.py backend/app/api/endpoints/config.py backend/app/services/public_url_service.py backend/app/schemas/system.py backend/app/api/endpoints/system.py backend/tests/test_public_url.py
git commit -m "feat(config): public base URL setting and resolver"
```

---

### Task 6: Frontend — public URL hook and the Playlist copy link (with token)

**Files:**
- Modify: `frontend/src/services/systemService.ts`, `frontend/src/hooks/useSystemServices.ts`, `frontend/src/services/configService.ts`
- Modify: `frontend/src/services/playlistService.ts:66-72`, `frontend/src/pages/Playlist.tsx:32-57`
- Test: `frontend/src/__tests__/Playlist.test.tsx`, `frontend/src/__tests__/playlistService.test.ts` (create if absent), `frontend/src/__tests__/systemService.test.ts` (create if absent)

**Interfaces:**
- Produces: `systemService.getPublicUrl(): Promise<PublicUrlResponse>`, `usePublicUrl()` (query key `PUBLIC_URL_QUERY_KEY = ['system', 'public-url']`), `configService.getPublicBaseUrl()/updatePublicBaseUrl(value)`, `getAbsolutePlaylistUrl(filters?, publicBaseUrl?)` (appends `token` from `getApiToken()`), `buildPublicUrl(path: string, publicBaseUrl?: string): string` (used by plans 2-4 for copy links).

- [ ] **Step 1: Write the failing tests**

Update `frontend/src/__tests__/Playlist.test.tsx`: add `import * as systemHooks from '../hooks/useSystemServices';`, `jest.mock('../hooks/useSystemServices');`, and in `beforeEach`:

```tsx
    window.localStorage.removeItem('apiToken');
    (systemHooks.usePublicUrl as jest.Mock).mockReturnValue({
      data: { url: 'http://scraper.lan:8000', source: 'setting', warnings: [] },
      isLoading: false,
    });
```

Change the three `http://localhost/api/v1/playlists/m3u?` expectations (lines 42, 88, 94) to `http://scraper.lan:8000/api/v1/playlists/m3u?` and add two tests:

```tsx
  it('falls back to the page origin while the public URL is loading', () => {
    (systemHooks.usePublicUrl as jest.Mock).mockReturnValue({ data: undefined, isLoading: true });
    renderPage();
    expect(urlField().value).toMatch(/^http:\/\/localhost\/api\/v1\/playlists\/m3u\?/);
  });

  it('appends the stored API token so players can authenticate', () => {
    window.localStorage.setItem('apiToken', 's3cret');
    renderPage();
    expect(urlField().value).toContain('token=s3cret');
    window.localStorage.removeItem('apiToken');
  });
```

Create `frontend/src/__tests__/playlistService.test.ts` (if the file exists, append the `describe` block):

```ts
import { getAbsolutePlaylistUrl } from '../services/playlistService';

describe('getAbsolutePlaylistUrl', () => {
  afterEach(() => window.localStorage.removeItem('apiToken'));

  it('resolves against the supplied public base URL', () => {
    expect(getAbsolutePlaylistUrl({ only_online: true }, 'https://scraper.example.com')).toBe(
      'https://scraper.example.com/api/v1/playlists/m3u?only_online=true'
    );
  });

  it('falls back to window.location.origin', () => {
    expect(getAbsolutePlaylistUrl({ only_online: true })).toBe('http://localhost/api/v1/playlists/m3u?only_online=true');
  });

  it('appends the API token as a query parameter', () => {
    window.localStorage.setItem('apiToken', 'a b');
    expect(getAbsolutePlaylistUrl({}, 'http://x')).toBe('http://x/api/v1/playlists/m3u?token=a+b');
  });
});
```

Create `frontend/src/__tests__/systemService.test.ts` (or append):

```ts
import apiClient from '../services/apiClient';
import { systemService } from '../services/systemService';

jest.mock('../services/apiClient', () => ({ __esModule: true, default: { get: jest.fn(), post: jest.fn() } }));

describe('systemService.getPublicUrl', () => {
  it('reads /v1/system/public-url', async () => {
    (apiClient.get as jest.Mock).mockResolvedValue({ data: { url: 'http://x', source: 'request', warnings: ['unset'] } });
    await expect(systemService.getPublicUrl()).resolves.toEqual({ url: 'http://x', source: 'request', warnings: ['unset'] });
    expect(apiClient.get).toHaveBeenCalledWith('/v1/system/public-url');
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd frontend && npm test -- Playlist.test.tsx playlistService.test.ts systemService.test.ts`
Expected: FAIL (`usePublicUrl` undefined, wrong origins).

- [ ] **Step 3: Implement**

`frontend/src/services/systemService.ts` — add:

```ts
export type PublicUrlSource = 'setting' | 'forwarded' | 'request';
export type PublicUrlWarning = 'localhost' | 'docker-internal' | 'unset' | 'proxied';

export interface PublicUrlResponse {
  url: string;
  source: PublicUrlSource;
  warnings: PublicUrlWarning[];
}
```

and in the `systemService` object:

```ts
  /** Origin that tuners, players and copied links must use to reach this server. */
  getPublicUrl: async (): Promise<PublicUrlResponse> => {
    const { data } = await apiClient.get<PublicUrlResponse>(`${BASE_URL}/public-url`);
    return data;
  },
```

`frontend/src/hooks/useSystemServices.ts` — add:

```ts
export const PUBLIC_URL_QUERY_KEY = ['system', 'public-url'] as const;

/** Resolved public base URL (spec 4.3); refetched after the setting changes. */
export const usePublicUrl = (options: Omit<UseQueryOptions<PublicUrlResponse>, 'queryKey' | 'queryFn'> = {}) =>
  useQuery<PublicUrlResponse>({
    queryKey: PUBLIC_URL_QUERY_KEY,
    queryFn: systemService.getPublicUrl,
    staleTime: 30_000,
    ...options,
  });
```

(import `PublicUrlResponse` from `../services/systemService`).

`frontend/src/services/configService.ts` — add to the object:

```ts
  /** Externally reachable origin (empty string = derived from the request). */
  getPublicBaseUrl: async (): Promise<string> => {
    const response = await apiClient.get<Setting>(`${BASE_URL}/public_base_url`);
    return response.data.value;
  },

  updatePublicBaseUrl: async (value: string): Promise<void> => {
    await apiClient.put(`${BASE_URL}/public_base_url`, { value });
  },
```

`frontend/src/services/playlistService.ts` — replace `getAbsolutePlaylistUrl` with:

```ts
import { getApiToken } from './apiToken';

/** Absolute URL for a backend path, resolved against the public base URL when known. */
export const buildPublicUrl = (pathWithQuery: string, publicBaseUrl?: string): string => {
  const origin = publicBaseUrl && publicBaseUrl.trim() !== '' ? publicBaseUrl : typeof window === 'undefined' ? '' : window.location.origin;
  if (!origin) return pathWithQuery;
  return new URL(pathWithQuery, origin.endsWith('/') ? origin : `${origin}/`).toString();
};

/** Absolute playlist URL for players on other devices (QR codes, copy button). */
export const getAbsolutePlaylistUrl = (filters?: PlaylistFilters, publicBaseUrl?: string): string => {
  const params = new URLSearchParams(playlistService.getPlaylistDownloadUrl(filters).split('?')[1] ?? '');
  const token = getApiToken();
  if (token) params.set('token', token);
  const query = params.toString();
  return buildPublicUrl(`/api/v1/playlists/m3u${query ? `?${query}` : ''}`, publicBaseUrl);
};
```

(keep the `import` at the top of the file with the others). `getPlaylistDownloadUrl` in dev mode returns `http://localhost:8000/api/v1/...`; splitting on `?` keeps only the query, so the absolute form always uses the public origin.

`frontend/src/pages/Playlist.tsx` — import `usePublicUrl` from `'../hooks/useSystemServices'`, add `const { data: publicUrl } = usePublicUrl();` after `useBaseUrls()`, and change line 57 to `const absolutePlaylistUrl = getAbsolutePlaylistUrl(effectiveFilters, publicUrl?.url);`.

- [ ] **Step 4: Run the frontend checks**

Run: `cd frontend && npm test -- Playlist.test.tsx playlistService.test.ts systemService.test.ts && npm run lint -- --max-warnings=0 && npm run typecheck`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/services/systemService.ts frontend/src/hooks/useSystemServices.ts frontend/src/services/configService.ts frontend/src/services/playlistService.ts frontend/src/pages/Playlist.tsx frontend/src/__tests__/Playlist.test.tsx frontend/src/__tests__/playlistService.test.ts frontend/src/__tests__/systemService.test.ts
git commit -m "feat(frontend): public URL hook; playlist copy link uses it and carries the API token"
```

---

### Task 7: LAN target guard

**Files:**
- Modify: `backend/app/utils/url_guard.py`
- Test: `backend/tests/test_url_guard.py`

**Interfaces:**
- Produces: `validate_lan_target(host: str, *, resolve: bool) -> None` raising `BlockedURLError`; `LAN_TARGET_BLOCKED_REASONS` not needed. Used by plans 3 and 4 on remote-player hosts and media-server URLs.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_url_guard.py`:

```python
from app.utils.url_guard import validate_lan_target


class TestLanTargetGuard:
    """validate_lan_target: LAN hosts are the point; metadata/link-local never (spec 4.4)."""

    @pytest.mark.parametrize("host", ["192.168.1.10", "10.0.0.5", "127.0.0.1", "8.8.8.8", "::1", "fd00::5"])
    def test_private_loopback_and_global_allowed_even_in_strict_mode(self, monkeypatch, host):
        monkeypatch.setenv("ALLOW_PRIVATE_SCRAPE_TARGETS", "false")
        validate_lan_target(host, resolve=False)

    @pytest.mark.parametrize("host", ["169.254.169.254", "::ffff:169.254.169.254", "169.254.10.1", "224.0.0.1", "0.0.0.0", "240.0.0.1", "fe80::1"])
    def test_metadata_link_local_multicast_unspecified_reserved_rejected(self, host):
        with pytest.raises(BlockedURLError):
            validate_lan_target(host, resolve=False)

    def test_hostname_passes_without_resolution(self, resolver):
        resolver({})
        validate_lan_target("jellyfin.lan", resolve=False)

    def test_hostname_resolving_to_metadata_is_rejected_when_resolving(self, resolver):
        resolver({"evil.lan": "169.254.169.254"})
        with pytest.raises(BlockedURLError, match="metadata|link-local"):
            validate_lan_target("evil.lan", resolve=True)

    def test_hostname_resolving_to_lan_passes_when_resolving(self, resolver, monkeypatch):
        monkeypatch.setenv("ALLOW_PRIVATE_SCRAPE_TARGETS", "false")
        resolver({"vlc.lan": "192.168.1.20"})
        validate_lan_target("vlc.lan", resolve=True)

    def test_empty_host_rejected(self):
        with pytest.raises(BlockedURLError):
            validate_lan_target("", resolve=False)
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_url_guard.py -k LanTarget`
Expected: FAIL (`ImportError`).

- [ ] **Step 3: Implement**

Append to `backend/app/utils/url_guard.py`:

```python
def _lan_target_reason(address) -> Optional[str]:
    address = _canonical_address(address)
    if address in METADATA_ADDRESSES:
        return "the cloud metadata endpoint"
    if address.is_link_local:
        return "a link-local address"
    if address.is_multicast:
        return "a multicast address"
    if address.is_unspecified:
        return "an unspecified address"
    if address.is_reserved:
        return "a reserved address"
    return None


def validate_lan_target(host: str, *, resolve: bool) -> None:
    """Validate a user-supplied LAN target (remote player host, media server).

    Private, loopback and global addresses are allowed regardless of
    ALLOW_PRIVATE_SCRAPE_TARGETS — talking to LAN devices is the feature.
    Metadata, link-local, multicast, unspecified and reserved addresses are
    always refused. With resolve=False only IP literals are checked; with
    resolve=True the host is resolved and every address is checked (call it
    immediately before each outbound request).
    """
    host = (host or "").strip().strip("[]")
    if not host:
        raise BlockedURLError("Target host is empty")
    try:
        candidates = [ipaddress.ip_address(host)]
    except ValueError:
        if not resolve:
            return
        candidates = _resolve_addresses(host)
    for address in candidates:
        reason = _lan_target_reason(address)
        if reason:
            raise BlockedURLError(f"Refusing to contact '{host}': resolves to {reason} ({_canonical_address(address)})")
```

Add `from typing import Optional` to the module imports.

- [ ] **Step 4: Run the guard tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_url_guard.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/url_guard.py backend/tests/test_url_guard.py
git commit -m "feat(guard): validate_lan_target for player and media-server hosts"
```

---

### Task 8: Redact `?token=` from uvicorn access logs

**Files:**
- Modify: `backend/app/utils/logging.py`
- Test: `backend/tests/test_logging_redaction.py`

**Interfaces:**
- Produces: `app.utils.logging.RedactTokenFilter` installed on the `uvicorn.access` logger by `setup_logging()`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_logging_redaction.py`:

```python
import logging

from app.utils.logging import RedactTokenFilter, setup_logging


def _record(args):
    return logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d', args, None)


def test_filter_redacts_token_in_args():
    record = _record(("127.0.0.1:1", "GET", "/api/v1/player/sessions/x/index.m3u8?token=T0p&x=1", "1.1", 200))
    assert RedactTokenFilter().filter(record) is True
    assert record.args[2] == "/api/v1/player/sessions/x/index.m3u8?token=[redacted]&x=1"
    assert "T0p" not in record.getMessage()


def test_filter_leaves_other_paths_alone():
    record = _record(("127.0.0.1:1", "GET", "/api/v1/health", "1.1", 200))
    RedactTokenFilter().filter(record)
    assert record.args[2] == "/api/v1/health"


def test_setup_logging_installs_the_filter_once():
    setup_logging()
    setup_logging()
    filters = [f for f in logging.getLogger("uvicorn.access").filters if isinstance(f, RedactTokenFilter)]
    assert len(filters) == 1
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_logging_redaction.py`
Expected: FAIL (`ImportError: RedactTokenFilter`).

- [ ] **Step 3: Implement**

In `backend/app/utils/logging.py` add near the top:

```python
import re

_TOKEN_RE = re.compile(r'([?&]token=)[^&\s"]*')


class RedactTokenFilter(logging.Filter):
    """Hide ?token= values in access-log lines (spec 4.4): native HLS players
    and copied links carry the API token in the query string."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(
                _TOKEN_RE.sub(r"\1[redacted]", arg) if isinstance(arg, str) else arg for arg in record.args
            )
        elif isinstance(record.msg, str):
            record.msg = _TOKEN_RE.sub(r"\1[redacted]", record.msg)
        return True
```

and inside `setup_logging()` before `return root_logger`:

```python
    access_logger = logging.getLogger('uvicorn.access')
    if not any(isinstance(f, RedactTokenFilter) for f in access_logger.filters):
        access_logger.addFilter(RedactTokenFilter())
```

- [ ] **Step 4: Run the test**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_logging_redaction.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/utils/logging.py backend/tests/test_logging_redaction.py
git commit -m "feat(logging): redact API tokens from uvicorn access logs"
```

---

### Task 9: Engine client

**Files:**
- Create: `backend/app/services/engine_client.py`
- Test: `backend/tests/test_engine_client.py`

**Interfaces:**
- Produces:
  ```python
  @dataclass(frozen=True)
  class EngineSession: content_id: str; pid: str; playback_url: str; stat_url: str; command_url: str; is_live: bool
  @dataclass(frozen=True)
  class EngineStats: status: str; peers: int; speed_down: int; speed_up: int
  class EngineUnavailableError(RuntimeError)
  class EngineRefusedError(RuntimeError)
  class EngineClient:
      def __init__(self, engine_url: str, client: httpx.Client | None = None)
      def start(self, content_id: str, pid: str | None = None) -> EngineSession
      def stop(self, session: EngineSession) -> None
      def stat(self, session: EngineSession) -> EngineStats
  def engine_url_from_settings(settings_repo: SettingsRepository) -> str   # DB ace_engine_url, http:// prefixed, no trailing slash
  def new_pid() -> str   # uuid4().hex
  ```

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_engine_client.py`:

```python
import json

import httpx
import pytest

from app.services.engine_client import (
    EngineClient, EngineRefusedError, EngineSession, EngineUnavailableError, engine_url_from_settings,
)

IH = "00c505e3e33687ecac47ef2a555497e66ebdc5af"
CID = "a" * 40


def _client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://engine:6878")


def test_start_parses_the_json_contract():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"response": {
            "playback_url": "http://engine:6878/ace/r/%s/tok" % IH,
            "stat_url": "http://engine:6878/ace/stat/%s/s1" % IH,
            "command_url": "http://engine:6878/ace/cmd/%s/s1" % IH,
            "is_live": 1, "playback_session_id": "s1"}, "error": None})

    session = EngineClient("http://engine:6878", client=_client(handler)).start(CID, pid="p1")
    assert seen["url"] == f"http://engine:6878/ace/getstream?id={CID}&pid=p1&format=json"
    assert session == EngineSession(content_id=CID, pid="p1", playback_url=f"http://engine:6878/ace/r/{IH}/tok",
                                    stat_url=f"http://engine:6878/ace/stat/{IH}/s1",
                                    command_url=f"http://engine:6878/ace/cmd/{IH}/s1", is_live=True)


def test_start_generates_a_pid_when_absent():
    def handler(request):
        assert len(request.url.params["pid"]) == 32
        return httpx.Response(200, json={"response": {"playback_url": "u", "stat_url": "s", "command_url": "c", "is_live": 0}, "error": None})
    assert EngineClient("http://engine:6878", client=_client(handler)).start(CID).is_live is False


def test_engine_error_is_refused():
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "To continue, you need to activate premium"})
    with pytest.raises(EngineRefusedError, match="activate premium"):
        EngineClient("http://engine:6878", client=_client(handler)).start(CID)


@pytest.mark.parametrize("make", [lambda r: httpx.Response(500, text="boom"), lambda r: (_ for _ in ()).throw(httpx.ConnectError("down"))])
def test_transport_failures_are_unavailable(make):
    with pytest.raises(EngineUnavailableError):
        EngineClient("http://engine:6878", client=_client(make)).start(CID)


def test_stop_and_stat():
    calls = []

    def handler(request):
        calls.append(str(request.url))
        if "cmd" in request.url.path:
            return httpx.Response(200, text="ok")
        return httpx.Response(200, json={"response": {"status": "dl", "peers": 7, "speed_down": 1200, "speed_up": 30}, "error": None})

    client = EngineClient("http://engine:6878", client=_client(handler))
    session = EngineSession(CID, "p", "u", "http://engine:6878/ace/stat/x/s", "http://engine:6878/ace/cmd/x/s", True)
    stats = client.stat(session)
    assert (stats.status, stats.peers, stats.speed_down, stats.speed_up) == ("dl", 7, 1200, 30)
    client.stop(session)  # errors are swallowed; the call must happen
    assert calls[-1] == "http://engine:6878/ace/cmd/x/s?method=stop"


def test_stop_swallows_errors():
    def handler(request):
        raise httpx.ConnectError("gone")
    EngineClient("http://engine:6878", client=_client(handler)).stop(EngineSession(CID, "p", "u", "s", "http://engine:6878/ace/cmd/x/s", True))


def test_engine_url_from_settings_normalizes(db_session):
    from app.repositories.settings_repository import SettingsRepository
    repo = SettingsRepository(db_session)
    repo.set_setting("ace_engine_url", "engine.lan:6878/")
    assert engine_url_from_settings(repo) == "http://engine.lan:6878"
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_engine_client.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

Create `backend/app/services/engine_client.py`:

```python
"""Thin client for the AceStream engine playback API (spec 4.1).

Used by the stream relay (tuner, remote players) and the web player. The
engine URL is the DB setting ``ace_engine_url`` read at call time.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

import httpx

from app.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

START_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
STAT_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


class EngineUnavailableError(RuntimeError):
    """The engine could not be reached or answered with a transport/5xx error."""


class EngineRefusedError(RuntimeError):
    """The engine answered but refused (its JSON carried an ``error``)."""


@dataclass(frozen=True)
class EngineSession:
    content_id: str
    pid: str
    playback_url: str
    stat_url: str
    command_url: str
    is_live: bool


@dataclass(frozen=True)
class EngineStats:
    status: str
    peers: int
    speed_down: int
    speed_up: int


def new_pid() -> str:
    return uuid.uuid4().hex


def engine_url_from_settings(settings_repo: SettingsRepository) -> str:
    url = (settings_repo.get_setting(SettingsRepository.ACE_ENGINE_URL) or "").strip()
    if not url:
        raise EngineUnavailableError("Acestream Engine URL is not configured")
    if not url.startswith("http"):
        url = f"http://{url}"
    return url.rstrip("/")


class EngineClient:
    def __init__(self, engine_url: str, client: Optional[httpx.Client] = None):
        self.engine_url = engine_url.rstrip("/")
        self._client = client or httpx.Client(timeout=START_TIMEOUT)

    def _get_json(self, url: str, params: Optional[dict] = None, timeout: httpx.Timeout = START_TIMEOUT) -> dict:
        try:
            response = self._client.get(url, params=params, timeout=timeout)
        except httpx.HTTPError as exc:
            raise EngineUnavailableError(f"Engine request failed: {exc}") from exc
        if response.status_code >= 500:
            raise EngineUnavailableError(f"Engine returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise EngineUnavailableError("Engine returned a non-JSON response") from exc
        error = payload.get("error") if isinstance(payload, dict) else None
        if error:
            raise EngineRefusedError(str(error))
        body = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(body, dict):
            raise EngineUnavailableError("Engine response has no 'response' object")
        return body

    def start(self, content_id: str, pid: Optional[str] = None) -> EngineSession:
        pid = pid or new_pid()
        body = self._get_json(
            f"{self.engine_url}/ace/getstream",
            params={"id": content_id, "pid": pid, "format": "json"},
        )
        try:
            return EngineSession(
                content_id=content_id,
                pid=pid,
                playback_url=str(body["playback_url"]),
                stat_url=str(body["stat_url"]),
                command_url=str(body["command_url"]),
                is_live=bool(int(body.get("is_live") or 0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EngineUnavailableError(f"Engine start response is incomplete: {body}") from exc

    def stop(self, session: EngineSession) -> None:
        try:
            self._client.get(session.command_url, params={"method": "stop"}, timeout=STAT_TIMEOUT)
        except httpx.HTTPError as exc:
            logger.warning("Engine stop for %s failed: %s", session.content_id, exc)

    def stat(self, session: EngineSession) -> EngineStats:
        body = self._get_json(session.stat_url, timeout=STAT_TIMEOUT)
        return EngineStats(
            status=str(body.get("status") or "unknown"),
            peers=int(body.get("peers") or 0),
            speed_down=int(body.get("speed_down") or 0),
            speed_up=int(body.get("speed_up") or 0),
        )
```

- [ ] **Step 4: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_engine_client.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/engine_client.py backend/tests/test_engine_client.py
git commit -m "feat(engine): thin engine playback client"
```

---

### Task 10: Stream relay (`ClosingStreamingResponse`, `relay_engine_stream`, registry, reaper)

**Files:**
- Create: `backend/app/services/stream_relay.py`
- Test: `backend/tests/test_stream_relay.py`

**Interfaces:**
- Produces:
  ```python
  class ClosingStreamingResponse(StreamingResponse)  # aclose()-guaranteed
  @dataclass class RelayInfo: id: str; content_id: str; client_label: str; started_at: float; bytes_sent: int; finished_at: float | None
  class RelayRegistry: def active(self) -> list[RelayInfo]; def count_active(self) -> int; def reap_finished(self, older_than_seconds: float = 30) -> int
  relay_registry = RelayRegistry()  # module singleton
  class EngineStreamError(RuntimeError)
  async def relay_engine_stream(engine: EngineClient, content_id: str, client_label: str, *, client_factory=None) -> AsyncIterator[bytes]
  RELAY_HEADERS = {"Content-Type": "video/mp2t", "Cache-Control": "no-store", "X-Accel-Buffering": "no"}
  ```
  The engine session is started in `run_in_threadpool` inside the generator (so the route can answer 502 before streaming: the generator's first iteration raises `EngineStreamError`/`EngineUnavailableError`/`EngineRefusedError`, and the route must call `await anext(iterator)` once to prime it — see Task 11).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_stream_relay.py`:

```python
"""Byte relay from the engine (spec 4.2)."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError
from app.services.stream_relay import (
    RELAY_HEADERS, ClosingStreamingResponse, EngineStreamError, RelayRegistry, relay_engine_stream,
)

IH = "0" * 40
BODY = b"\x47" * 188 * 50


def _fake_engine(calls, *, redirect_host="engine", content_status=200):
    """MockTransport handler: JSON start -> 302 -> bytes; records stop calls."""
    def handler(request):
        calls.append((request.method, str(request.url)))
        path = request.url.path
        if path == "/ace/getstream":
            return httpx.Response(200, json={"response": {
                "playback_url": f"http://engine:6878/ace/r/{IH}/tok",
                "stat_url": f"http://engine:6878/ace/stat/{IH}/s",
                "command_url": f"http://engine:6878/ace/cmd/{IH}/s", "is_live": 1}, "error": None})
        if path.startswith("/ace/r/"):
            return httpx.Response(302, headers={"Location": f"http://{redirect_host}:6878/content/{IH}/1"})
        if path.startswith("/content/"):
            return httpx.Response(content_status, content=BODY if content_status == 200 else b"", headers={"Content-Type": "video/mp2t"})
        if path.startswith("/ace/cmd/"):
            return httpx.Response(200, text="ok")
        return httpx.Response(404)
    return handler


def _engine_and_factory(handler):
    sync_client = httpx.Client(transport=httpx.MockTransport(handler))
    engine = EngineClient("http://engine:6878", client=sync_client)

    def factory(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(handler), **kwargs)
    return engine, factory


def _collect(gen):
    async def run():
        chunks = []
        async for chunk in gen:
            chunks.append(chunk)
        return b"".join(chunks)
    return asyncio.run(run())


def test_relay_follows_engine_redirect_and_stops_once():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls))
    body = _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert body == BODY
    stops = [u for m, u in calls if "/ace/cmd/" in u]
    assert stops == [f"http://engine:6878/ace/cmd/{IH}/s?method=stop"]


def test_redirect_to_another_host_is_refused():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls, redirect_host="evil"))
    with pytest.raises(EngineStreamError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert sum("/ace/cmd/" in u for _, u in calls) == 1


def test_non_200_upstream_is_refused_with_one_stop():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls, content_status=500))
    with pytest.raises(EngineStreamError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))
    assert sum("/ace/cmd/" in u for _, u in calls) == 1


def test_engine_refusal_propagates_before_any_bytes():
    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "activate premium"})
    engine, factory = _engine_and_factory(handler)
    with pytest.raises(EngineRefusedError):
        _collect(relay_engine_stream(engine, IH, "test", client_factory=factory))


def test_cancelled_consumer_stops_engine_session_exactly_once():
    calls = []
    engine, factory = _engine_and_factory(_fake_engine(calls))

    async def run():
        gen = relay_engine_stream(engine, IH, "test", client_factory=factory)
        await gen.__anext__()
        await gen.aclose()
    asyncio.run(run())
    assert sum("/ace/cmd/" in u for _, u in calls) == 1


def test_closing_streaming_response_closes_generator_on_client_disconnect():
    closed = asyncio.Event()

    async def forever():
        try:
            while True:
                yield b"x" * 1024
                await asyncio.sleep(0)
        finally:
            closed.set()

    app = FastAPI()

    @app.get("/s")
    async def stream():
        return ClosingStreamingResponse(forever(), headers=RELAY_HEADERS)

    with TestClient(app) as client:
        with client.stream("GET", "/s") as response:
            assert response.headers["content-type"] == "video/mp2t"
            assert response.headers["x-accel-buffering"] == "no"
            next(response.iter_bytes())
    assert closed.is_set()


def test_registry_tracks_and_reaps():
    registry = RelayRegistry()
    info = registry.open("c" * 40, "vlc")
    assert registry.count_active() == 1
    registry.close(info.id)
    assert registry.count_active() == 0
    assert registry.reap_finished(older_than_seconds=0) == 1
    assert registry.active() == []
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_stream_relay.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement**

Create `backend/app/services/stream_relay.py`:

```python
"""Relay engine MPEG-TS bytes to a client (spec 4.2).

- ClosingStreamingResponse guarantees the body generator's ``finally`` runs
  as soon as the client goes away (Starlette itself never calls aclose()).
- relay_engine_stream starts an engine session, follows the engine's own
  302 (only to the engine host), streams 64 KiB chunks and stops the session
  on every exit path.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Dict, List, Optional
from urllib.parse import urlsplit

import anyio
import httpx
from fastapi.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse

from app.services.engine_client import EngineClient, EngineSession

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024
RELAY_HEADERS = {"Content-Type": "video/mp2t", "Cache-Control": "no-store", "X-Accel-Buffering": "no"}
RELAY_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)


class EngineStreamError(RuntimeError):
    """The engine session started but the byte stream could not be opened."""


class ClosingStreamingResponse(StreamingResponse):
    async def __call__(self, scope, receive, send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            aclose = getattr(self.body_iterator, "aclose", None)
            if aclose is not None:
                with anyio.CancelScope(shield=True):
                    try:
                        await aclose()
                    except Exception:  # noqa: BLE001 - cleanup must never raise into the server
                        logger.exception("Relay generator close failed")


@dataclass
class RelayInfo:
    id: str
    content_id: str
    client_label: str
    started_at: float
    bytes_sent: int = 0
    finished_at: Optional[float] = None


class RelayRegistry:
    def __init__(self) -> None:
        self._relays: Dict[str, RelayInfo] = {}

    def open(self, content_id: str, client_label: str) -> RelayInfo:
        info = RelayInfo(id=uuid.uuid4().hex, content_id=content_id, client_label=client_label, started_at=time.time())
        self._relays[info.id] = info
        return info

    def close(self, relay_id: str) -> None:
        info = self._relays.get(relay_id)
        if info is not None and info.finished_at is None:
            info.finished_at = time.time()

    def active(self) -> List[RelayInfo]:
        return [info for info in self._relays.values() if info.finished_at is None]

    def count_active(self) -> int:
        return len(self.active())

    def reap_finished(self, older_than_seconds: float = 30.0) -> int:
        cutoff = time.time() - older_than_seconds
        stale = [rid for rid, info in self._relays.items() if info.finished_at is not None and info.finished_at <= cutoff]
        for rid in stale:
            del self._relays[rid]
        return len(stale)


relay_registry = RelayRegistry()


def _default_client_factory(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


async def relay_engine_stream(
    engine: EngineClient,
    content_id: str,
    client_label: str,
    *,
    client_factory: Optional[Callable[..., httpx.AsyncClient]] = None,
    registry: Optional[RelayRegistry] = None,
) -> AsyncIterator[bytes]:
    """Yield MPEG-TS bytes for ``content_id``. Raises EngineUnavailableError /
    EngineRefusedError (session start) or EngineStreamError (stream open)
    before the first byte; stops the engine session on every exit."""
    registry = registry or relay_registry
    factory = client_factory or _default_client_factory
    session: EngineSession = await run_in_threadpool(engine.start, content_id)
    info = registry.open(content_id, client_label)
    engine_host = urlsplit(engine.engine_url).hostname
    try:
        async with factory(follow_redirects=True, max_redirects=3, timeout=RELAY_TIMEOUT) as client:
            async with client.stream("GET", session.playback_url) as response:
                final_host = response.url.host
                if final_host != engine_host:
                    raise EngineStreamError(f"Engine redirected to an unexpected host: {final_host}")
                if response.status_code != 200:
                    raise EngineStreamError(f"Engine stream returned HTTP {response.status_code}")
                async for chunk in response.aiter_bytes(CHUNK_SIZE):
                    info.bytes_sent += len(chunk)
                    yield chunk
    finally:
        registry.close(info.id)
        with anyio.CancelScope(shield=True):
            await run_in_threadpool(engine.stop, session)
```

- [ ] **Step 4: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_stream_relay.py`
Expected: PASS. If `test_closing_streaming_response_closes_generator_on_client_disconnect` hangs, wrap the `next(response.iter_bytes())` read in the `with client.stream(...)` block exactly as shown (leaving the block closes the connection).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/stream_relay.py backend/tests/test_stream_relay.py
git commit -m "feat(relay): engine byte relay with guaranteed cleanup and registry"
```

---

### Task 11: Tuner network gate and `/tuner/stream/<id>.ts`

**Files:**
- Create: `backend/app/services/tuner_network.py`, `backend/app/api/endpoints/tuner.py`
- Modify: `backend/main.py` (include `hdhr_router`; SPA fallback skips `/tuner`; relay reaper in lifespan)
- Test: `backend/tests/test_tuner_network.py`, `backend/tests/test_api_token_auth.py`

**Interfaces:**
- Produces:
  ```python
  # app/services/tuner_network.py
  @dataclass class Denial: client_ip: str; peer: str; path: str; at: float
  class TunerNetworkGate:
      def __init__(self, allowed_spec: str)            # parse_trusted() semantics
      def is_allowed(self, host: str | None) -> bool
      def record_denial(self, client_ip, peer, path) -> None
      def recent_denials(self) -> list[Denial]         # last 20, newest first
      @property def allowed_networks(self) -> list[str]
      def classify_source(self, peer: str, forwarded: bool) -> Literal["direct","forwarded","docker-gateway","loopback"]
  def get_tuner_gate() -> TunerNetworkGate                 # built from Settings, cached per settings object
  async def require_tuner_network(request: Request) -> None  # 403 APIError TUNER_NETWORK_DENIED
  # app/api/endpoints/tuner.py
  hdhr_router = APIRouter(prefix="/tuner", dependencies=[Depends(require_tuner_network)], tags=["hdhomerun"])
  router = APIRouter()   # empty here; plan 4 adds /settings and /status
  GET|HEAD /tuner/stream/{content_id}.ts ; GET /tuner/{path:path} -> 404 JSON {"detail": "Unknown tuner path"}
  ```

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_tuner_network.py`:

```python
"""Token-free /tuner/* routes are gated by TUNER_ALLOWED_NETWORKS on both the
raw peer and the forwarded client (spec 4.4)."""
import httpx
import pytest

from app.config.settings import get_settings
from app.services.tuner_network import TunerNetworkGate, get_tuner_gate

IH = "0" * 40


@pytest.fixture
def gate_env(monkeypatch):
    def apply(spec: str):
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", spec)
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()
    yield apply
    get_settings.cache_clear()
    get_tuner_gate.cache_clear()


@pytest.mark.parametrize(("spec", "host", "expected"), [
    ("192.168.0.0/16", "192.168.1.5", True),
    ("192.168.0.0/16", "::ffff:192.168.1.5", True),
    ("192.168.0.0/16", "203.0.113.4", False),
    ("*", "203.0.113.4", True),
    ("", "127.0.0.1", False),
    ("testclient", "testclient", True),
])
def test_gate_membership(spec, host, expected):
    assert TunerNetworkGate(spec).is_allowed(host) is expected


def test_default_allows_tailscale_and_link_local_but_not_public():
    gate = TunerNetworkGate(get_settings().TUNER_ALLOWED_NETWORKS)
    assert gate.is_allowed("100.64.0.1")
    assert gate.is_allowed("fe80::1")
    assert not gate.is_allowed("8.8.8.8")


def test_classify_source():
    gate = TunerNetworkGate("*")
    assert gate.classify_source("127.0.0.1", False) == "loopback"
    assert gate.classify_source("172.17.0.1", False) == "docker-gateway"
    assert gate.classify_source("192.168.65.1", False) == "docker-gateway"
    assert gate.classify_source("192.168.1.9", False) == "direct"
    assert gate.classify_source("172.17.0.1", True) == "forwarded"


def test_denials_ring_buffer():
    gate = TunerNetworkGate("10.0.0.0/8")
    for i in range(25):
        gate.record_denial(f"203.0.113.{i}", f"203.0.113.{i}", "/tuner/lineup.json")
    denials = gate.recent_denials()
    assert len(denials) == 20
    assert denials[0].client_ip == "203.0.113.24"


def test_stream_route_denied_outside_allowlist(client, gate_env):
    gate_env("10.0.0.0/8")
    response = client.get(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 403
    body = response.json()["error"]
    assert body["code"] == "TUNER_NETWORK_DENIED"
    assert body["context"]["client_ip"] == "testclient"
    assert body["context"]["allowed_networks"] == ["10.0.0.0/8"]
    assert get_tuner_gate().recent_denials()[0].path == f"/tuner/stream/{IH}.ts"


def test_spoofed_forwarded_for_cannot_pass_a_narrow_allowlist(client, gate_env, monkeypatch):
    # Peer "testclient" is trusted for forwarding but not in the tuner allowlist.
    gate_env("192.168.1.20/32")
    import main
    from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted
    for layer in main.app.user_middleware:
        if layer.cls is ForwardedHeadersMiddleware:
            layer.kwargs["trusted"] = parse_trusted("testclient")
    main.app.middleware_stack = None
    try:
        response = client.get(f"/tuner/stream/{IH}.ts", headers={"X-Forwarded-For": "192.168.1.20"})
        assert response.status_code == 403
    finally:
        for layer in main.app.user_middleware:
            if layer.cls is ForwardedHeadersMiddleware:
                layer.kwargs["trusted"] = parse_trusted(get_settings().FORWARDED_ALLOW_IPS)
        main.app.middleware_stack = None


def test_unknown_tuner_path_is_json_404_not_spa(client, gate_env):
    gate_env("*")
    response = client.get("/tuner/does-not-exist.json")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"detail": "Unknown tuner path"}


def test_head_stream_answers_headers_without_engine(client, gate_env, monkeypatch):
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    monkeypatch.setattr(tuner_module, "_engine", lambda db: (_ for _ in ()).throw(AssertionError("engine must not be called on HEAD")))
    response = client.head(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 200
    assert response.headers["content-type"] == "video/mp2t"
    assert response.headers["cache-control"] == "no-store"


def test_stream_route_relays_bytes_and_ignores_transcode_param(client, gate_env, monkeypatch):
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    from app.services.engine_client import EngineClient
    body = b"\x47" * 188 * 10

    def handler(request):
        p = request.url.path
        if p == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        if p.startswith("/content/"):
            return httpx.Response(200, content=body, headers={"Content-Type": "video/mp2t"})
        return httpx.Response(200, text="ok")

    monkeypatch.setattr(tuner_module, "_engine", lambda db: EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler))))
    monkeypatch.setattr(tuner_module, "_relay_client_factory", lambda **kw: httpx.AsyncClient(transport=httpx.MockTransport(handler), **kw))
    response = client.get(f"/tuner/stream/{IH}.ts?transcode=heavy")
    assert response.status_code == 200
    assert response.content == body


def test_stream_route_maps_engine_refusal_to_502(client, gate_env, monkeypatch):
    gate_env("*")
    import app.api.endpoints.tuner as tuner_module
    from app.services.engine_client import EngineClient

    def handler(request):
        return httpx.Response(200, json={"response": None, "error": "activate premium"})

    monkeypatch.setattr(tuner_module, "_engine", lambda db: EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler))))
    response = client.get(f"/tuner/stream/{IH}.ts")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ENGINE_REFUSED"


def test_invalid_content_id_is_422(client, gate_env):
    gate_env("*")
    assert client.get("/tuner/stream/not-hex.ts").status_code == 422
```

Append to `backend/tests/test_api_token_auth.py` inside `TestTokenEnforced`:

```python
    def test_tuner_routes_stay_public(self, client, token_enabled, monkeypatch):
        from app.config.settings import get_settings
        from app.services.tuner_network import get_tuner_gate
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
        get_settings.cache_clear(); get_tuner_gate.cache_clear()
        try:
            response = client.head("/tuner/stream/" + "0" * 40 + ".ts")
            assert response.status_code == 200
            assert client.get("/tuner/nope").status_code == 404
        finally:
            get_settings.cache_clear(); get_tuner_gate.cache_clear()
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_network.py backend/tests/test_api_token_auth.py`
Expected: FAIL (`ModuleNotFoundError` / 404 HTML).

- [ ] **Step 3: Implement the gate**

Create `backend/app/services/tuner_network.py`:

```python
"""Network allowlist for the token-free /tuner/* routes (spec 4.4)."""
from __future__ import annotations

import ipaddress
import logging
import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Deque, List, Literal, Optional

from fastapi import Request

from app.api.error_handlers import APIError
from app.config.settings import get_settings
from app.middleware.forwarded import TrustedPeers, parse_trusted

logger = logging.getLogger(__name__)

ClientSource = Literal["direct", "forwarded", "docker-gateway", "loopback"]
_DOCKER_DESKTOP = ipaddress.ip_network("192.168.65.0/24")
_DOCKER_BRIDGE = ipaddress.ip_network("172.16.0.0/12")


@dataclass
class Denial:
    client_ip: str
    peer: str
    path: str
    at: float


class TunerNetworkGate:
    def __init__(self, allowed_spec: str):
        self.allowed_spec = allowed_spec
        self._trusted: TrustedPeers = parse_trusted(allowed_spec)
        self._denials: Deque[Denial] = deque(maxlen=20)
        self._warned: set = set()

    @property
    def allowed_networks(self) -> List[str]:
        return [token.strip() for token in self.allowed_spec.split(",") if token.strip()]

    def is_allowed(self, host: Optional[str]) -> bool:
        return self._trusted.contains(host)

    def record_denial(self, client_ip: str, peer: str, path: str) -> None:
        self._denials.appendleft(Denial(client_ip=client_ip, peer=peer, path=path, at=time.time()))
        if client_ip not in self._warned:
            self._warned.add(client_ip)
            logger.warning(
                "Tuner request from %s (peer %s) denied by TUNER_ALLOWED_NETWORKS=%s", client_ip, peer, self.allowed_spec
            )

    def recent_denials(self) -> List[Denial]:
        return list(self._denials)

    @staticmethod
    def classify_source(peer: Optional[str], forwarded: bool) -> ClientSource:
        if forwarded:
            return "forwarded"
        try:
            address = ipaddress.ip_address((peer or "").strip("[]"))
        except ValueError:
            return "direct"
        mapped = getattr(address, "ipv4_mapped", None)
        address = mapped if mapped is not None else address
        if address.is_loopback:
            return "loopback"
        if address in _DOCKER_DESKTOP:
            return "docker-gateway"
        if address in _DOCKER_BRIDGE and str(address).endswith(".1"):
            return "docker-gateway"
        return "direct"


@lru_cache(maxsize=1)
def get_tuner_gate() -> TunerNetworkGate:
    return TunerNetworkGate(get_settings().TUNER_ALLOWED_NETWORKS)


async def require_tuner_network(request: Request) -> None:
    gate = get_tuner_gate()
    peer = (getattr(request.state, "peer", None) or (None, 0))[0]
    client_ip = request.client.host if request.client else None
    if gate.is_allowed(peer) and gate.is_allowed(client_ip):
        return
    gate.record_denial(client_ip or "?", peer or "?", request.url.path)
    raise APIError(
        code="TUNER_NETWORK_DENIED",
        message="This address is not allowed to use the tuner routes (TUNER_ALLOWED_NETWORKS)",
        status_code=403,
        context={"client_ip": client_ip, "peer": peer, "allowed_networks": gate.allowed_networks},
    )
```

- [ ] **Step 4: Implement the router**

Create `backend/app/api/endpoints/tuner.py`:

```python
"""HDHomeRun-style tuner routes (spec 7.1). This plan ships the byte relay and
the JSON 404; plan 4 adds discover/lineup/guide and the token-gated
settings/status router."""
from __future__ import annotations

import re

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError, engine_url_from_settings
from app.services.stream_relay import RELAY_HEADERS, ClosingStreamingResponse, EngineStreamError, relay_engine_stream
from app.services.tuner_network import require_tuner_network

hdhr_router = APIRouter(prefix="/tuner", dependencies=[Depends(require_tuner_network)], tags=["hdhomerun"])
router = APIRouter()  # /api/v1/tuner settings + status (plan 4)

_CONTENT_ID = re.compile(r"^[0-9a-fA-F]{40}$")


def _engine(db: Session) -> EngineClient:
    return EngineClient(engine_url_from_settings(SettingsRepository(db)))


def _relay_client_factory(**kwargs) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


def _validate_content_id(content_id: str) -> str:
    if not _CONTENT_ID.match(content_id):
        raise HTTPException(status_code=422, detail="content_id must be a 40-character hex string")
    return content_id.lower()


@hdhr_router.api_route("/stream/{content_id}.ts", methods=["GET", "HEAD"], summary="MPEG-TS relay of one channel")
async def tuner_stream(content_id: str, request: Request, db: Session = Depends(get_db)):
    """Relays the engine's MPEG-TS bytes. Unknown query params (transcode,
    duration) are ignored. HEAD answers headers only and never starts a
    session."""
    content_id = _validate_content_id(content_id)
    if request.method == "HEAD":
        return Response(status_code=200, headers=RELAY_HEADERS)
    engine = _engine(db)
    peer = request.client.host if request.client else "?"
    iterator = relay_engine_stream(engine, content_id, f"tuner:{peer}", client_factory=_relay_client_factory)
    try:
        first = await iterator.__anext__()
    except EngineRefusedError as exc:
        raise APIError(code="ENGINE_REFUSED", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    except EngineUnavailableError as exc:
        raise APIError(code="ENGINE_UNAVAILABLE", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    except EngineStreamError as exc:
        raise APIError(code="ENGINE_STREAM_FAILED", message=str(exc), status_code=502, context={"content_id": content_id}) from exc
    except StopAsyncIteration:
        return Response(status_code=200, headers=RELAY_HEADERS)

    async def body():
        try:
            yield first
            async for chunk in iterator:
                yield chunk
        finally:
            await iterator.aclose()

    return ClosingStreamingResponse(body(), headers=RELAY_HEADERS)


@hdhr_router.api_route("/{path:path}", methods=["GET", "HEAD", "POST"], include_in_schema=False)
async def tuner_not_found(path: str):
    # Tuner clients must never receive the SPA's index.html for a typo'd path.
    raise HTTPException(status_code=404, detail="Unknown tuner path")
```

The catch-all must be declared **last** in this file; plan 4 inserts its routes above it.

- [ ] **Step 5: Wire it in `main.py`**

After `app.include_router(api_router, ...)` add:

```python
# HDHomeRun-style tuner routes: token-free by design (tuner clients cannot send
# credentials), gated by TUNER_ALLOWED_NETWORKS inside the router (spec 4.4).
from app.api.endpoints import tuner as tuner_endpoints
app.include_router(tuner_endpoints.hdhr_router)
```

In `spa_server` change the condition to:

```python
    if exc.status_code == 404 and not request.url.path.startswith(("/api", "/tuner")):
```

In `lifespan()` add a relay reaper task: after `_schedule_deferred_migration()`:

```python
    from app.services.stream_relay import relay_registry
    import asyncio

    async def _reap_relays():
        while True:
            await asyncio.sleep(30)
            relay_registry.reap_finished(older_than_seconds=30)

    reaper = asyncio.create_task(_reap_relays())
    try:
        yield
    finally:
        reaper.cancel()
        task_service.shutdown()
```

(replace the existing `try: yield / finally: task_service.shutdown()` block).

- [ ] **Step 6: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_tuner_network.py backend/tests/test_api_token_auth.py backend/tests/test_legacy_playlist_routes.py backend/tests/test_error_contracts.py`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/tuner_network.py backend/app/api/endpoints/tuner.py backend/main.py backend/tests/test_tuner_network.py backend/tests/test_api_token_auth.py
git commit -m "feat(tuner): network-gated /tuner/stream relay and JSON 404 catch-all"
```

---

### Task 12: Stream ranking helper and sorted TV-channel payloads

**Files:**
- Create: `backend/app/services/stream_ranking.py`
- Modify: `backend/app/services/playlist_service.py:172,219-231`, `backend/app/schemas/channel.py:99-109`, `backend/app/api/endpoints/tv_channels.py:217-227`
- Test: `backend/tests/test_stream_ranking.py`, `backend/tests/test_tv_channels.py`

**Interfaces:**
- Produces: `score_acestream(stream) -> int` and `sort_streams_curated(streams) -> list` (duck-typed: ORM rows or DTOs with `is_online`, `logo`, `tvg_id`, `tvg_name`, `id`); `TVChannelResponse.acestream_channels` is always in curated order; `GET /api/v1/tv-channels/{id}/acestreams` too.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_stream_ranking.py`:

```python
from types import SimpleNamespace

from app.services.stream_ranking import score_acestream, sort_streams_curated


def _s(id, **kw):
    base = dict(is_online=None, logo=None, tvg_id=None, tvg_name=None)
    base.update(kw)
    return SimpleNamespace(id=id, **base)


def test_weights_match_the_playlist_contract():
    assert score_acestream(_s("a")) == 0
    assert score_acestream(_s("a", is_online=True)) == 10
    assert score_acestream(_s("a", logo="l")) == 3
    assert score_acestream(_s("a", tvg_id="t")) == 2
    assert score_acestream(_s("a", tvg_name="n")) == 1
    assert score_acestream(_s("a", is_online=True, logo="l", tvg_id="t", tvg_name="n")) == 16


def test_sort_is_score_desc_then_id():
    streams = [_s("c", logo="l"), _s("b", is_online=True), _s("a", is_online=True)]
    assert [s.id for s in sort_streams_curated(streams)] == ["a", "b", "c"]
```

Append to `backend/tests/test_tv_channels.py`:

```python
def test_acestream_channels_returned_in_curated_order(client, db_session):
    """Best stream first (online, then logo/tvg metadata), regardless of insertion order."""
    from app.models.models import AcestreamChannel, TVChannel

    tv = TVChannel(name="Order Test")
    db_session.add(tv)
    db_session.flush()
    offline_with_logo = AcestreamChannel(id="f" * 40, name="offline", logo="l", is_online=False, tv_channel_id=tv.id)
    online_plain = AcestreamChannel(id="e" * 40, name="online", is_online=True, tv_channel_id=tv.id)
    online_rich = AcestreamChannel(id="d" * 40, name="rich", is_online=True, logo="l", tvg_id="x", tv_channel_id=tv.id)
    db_session.add_all([offline_with_logo, online_plain, online_rich])
    db_session.commit()

    expected = ["d" * 40, "e" * 40, "f" * 40]
    detail = client.get(f"/api/v1/tv-channels/{tv.id}").json()
    assert [s["id"] for s in detail["acestream_channels"]] == expected
    listing = client.get("/api/v1/tv-channels/?search=Order").json()["items"][0]
    assert [s["id"] for s in listing["acestream_channels"]] == expected
    acestreams = client.get(f"/api/v1/tv-channels/{tv.id}/acestreams").json()
    assert [s["id"] for s in acestreams] == expected
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_stream_ranking.py backend/tests/test_tv_channels.py -k "ranking or curated_order"`
Expected: FAIL.

- [ ] **Step 3: Implement**

Create `backend/app/services/stream_ranking.py`:

```python
"""Best-stream-first ordering shared by playlists, the tuner lineup and the
TV-channel API (spec 5.2). Duck-typed: works on ORM rows and DTOs."""
from __future__ import annotations

from typing import Iterable, List, TypeVar

T = TypeVar("T")


def score_acestream(stream) -> int:
    score = 0
    if getattr(stream, "is_online", None):
        score += 10
    if getattr(stream, "logo", None):
        score += 3
    if getattr(stream, "tvg_id", None):
        score += 2
    if getattr(stream, "tvg_name", None):
        score += 1
    return score


def sort_streams_curated(streams: Iterable[T]) -> List[T]:
    return sorted(streams, key=lambda s: (-score_acestream(s), getattr(s, "id", "")))
```

`backend/app/services/playlist_service.py`: import `from app.services.stream_ranking import score_acestream, sort_streams_curated`; change line 172 to `streams = sort_streams_curated(streams)`; replace the body of `_score_acestream` with `return score_acestream(stream)` (keep the staticmethod as an alias).

`backend/app/schemas/channel.py`: import `field_validator` from pydantic and `sort_streams_curated`; in `TVChannelResponse` add:

```python
    @field_validator("acestream_channels", mode="after")
    @classmethod
    def _curated_order(cls, value: List[AcestreamChannelResponse]) -> List[AcestreamChannelResponse]:
        return sort_streams_curated(value)
```

(`sort_streams_curated` has no model imports, so no cycle.)

`backend/app/api/endpoints/tv_channels.py:227`: `return sort_streams_curated(tv_channel.acestream_channels)` (import it).

- [ ] **Step 4: Run the tests**

Run: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_stream_ranking.py backend/tests/test_tv_channels.py backend/tests/test_curated_playlists.py backend/tests/test_playlists.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/stream_ranking.py backend/app/services/playlist_service.py backend/app/schemas/channel.py backend/app/api/endpoints/tv_channels.py backend/tests/test_stream_ranking.py backend/tests/test_tv_channels.py
git commit -m "feat(tv-channels): curated stream ordering shared by API, playlist and tuner"
```

---

### Task 13: OpenAPI/codegen, full suite, docs touch-ups

**Files:**
- Modify: `backend/openapi.json`, `frontend/src/types/api-generated.ts` (generated)
- Modify: `wiki/Configuration.md` (env table), `docs/ops/reverse-proxy.md`

- [ ] **Step 1: Regenerate the contract artifacts**

Run:
```bash
backend/venv/bin/python backend/scripts/dump_openapi.py
cd frontend && npm run codegen && cd ..
git diff --stat backend/openapi.json frontend/src/types/api-generated.ts
```
Expected: both files change (new `public_base_url` routes, `PublicUrlResponse`, `PublicBaseUrlUpdate`).

- [ ] **Step 2: Docs**

`wiki/Configuration.md` — add rows to the environment table (create a "Media integrations" subsection if the table is per-feature):

```markdown
| `PUBLIC_BASE_URL` | (empty) | Origin (`http://host:port`) that Jellyfin/Plex/VLC use to reach this server; editable under Integrations. Empty derives it from each request. |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` | Peers whose `X-Forwarded-*` headers the app trusts (uvicorn's own handling is disabled). |
| `TUNER_ALLOWED_NETWORKS` | `127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10` | Networks allowed to use the token-free `/tuner/*` routes; `*` disables the check. |
| `PLAYER_HLS_DIR` | `/tmp/acestream-player` | Where the web player writes HLS segments (`/dev/shm/acestream-player` with a larger `shm_size` keeps them in RAM). |
| `PLAYER_MAX_SESSIONS` | `3` | Maximum channels the web player prepares at once. |
| `PLAYER_START_TIMEOUT_SECONDS` | `45` | Seconds a web-player session may stay in "starting" before it is reported as stalled. |
| `FFMPEG_BINARY_PATH` | (image default `/opt/ffmpeg/bin/ffmpeg`) | ffmpeg used by the web player; empty falls back to `ffmpeg` on `PATH`. |
| `MEDIA_SERVER_MIN_REFRESH_MINUTES` | `30` | Minimum minutes between automatic Jellyfin/Plex guide refreshes (`0` disables the debounce). |
```

`docs/ops/reverse-proxy.md` — in the "forwarded headers are enough" paragraph (lines 44-49) replace with: forwarded headers are honoured only when the proxy's address is inside `FORWARDED_ALLOW_IPS` (default: loopback and private ranges); the app reads `X-Forwarded-Proto`, `X-Forwarded-Host` and `X-Forwarded-For` itself, so keep `--no-proxy-headers` and `--timeout-graceful-shutdown 3` in any compose `command:` override; set `PUBLIC_BASE_URL` when the proxy rewrites `Host` or mounts the app under a sub-path. Add a sentence that `/tuner/*` must not sit behind proxy basic auth (full nginx/Caddy/Traefik snippets land in plan 4).

- [ ] **Step 3: Run the canonical suites**

Run:
```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker
cd frontend && npm run lint -- --max-warnings=0 && npm run typecheck && CI=true npm test -- --watch=false && npm run build && cd ..
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/validate_command_builder.sh
```
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/openapi.json frontend/src/types/api-generated.ts wiki/Configuration.md docs/ops/reverse-proxy.md
git commit -m "chore(contracts): regenerate OpenAPI/types; document media env knobs and proxy trust"
```
