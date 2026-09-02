"""Status and restart of the sidecar services a container may run next to the
app: AceStream engine, Acexy, the embedded IPFS daemon, ZeroNet and WARP.

Whether a service is *installed* comes from the image flavor (IMAGE_HAS_*),
whether it is *enabled* from ENABLE_*, and whether it is *running* from a live
probe. When the entrypoint supervises the process it records a pid file under
SUPERVISOR_RUN_DIR; that is what makes a restart possible from the app.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import signal
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests

from app.config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_RUN_DIR = "/run/acestream-scraper"
PROBE_TIMEOUT_SECONDS = 2.0
SERVICE_NAMES = ("acestream", "acexy", "ipfs", "zeronet", "warp")


class ServiceNotFoundError(KeyError):
    """Unknown service name."""


class ServiceNotManagedError(RuntimeError):
    """The service is not supervised by this container, so it cannot be restarted from here."""


def _flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class ProbeResult:
    ok: bool
    message: str = ""
    version: Optional[str] = None


@dataclass
class ProcessInfo:
    pid: Optional[int] = None
    alive: bool = False
    uptime_seconds: Optional[int] = None


class SystemServicesService:
    def __init__(
        self,
        run_dir: Optional[str] = None,
        external_engine_url: Optional[str] = None,
        http_get: Optional[Callable[..., requests.Response]] = None,
        http_post: Optional[Callable[..., requests.Response]] = None,
    ) -> None:
        self.run_dir = Path(run_dir or os.environ.get("SUPERVISOR_RUN_DIR", DEFAULT_RUN_DIR))
        self.external_engine_url = (external_engine_url or getattr(settings, "ACE_ENGINE_URL", "http://localhost:6878")).rstrip("/")
        self._get = http_get or (lambda url, **kw: requests.get(url, timeout=PROBE_TIMEOUT_SECONDS, **kw))
        self._post = http_post or (lambda url, **kw: requests.post(url, timeout=PROBE_TIMEOUT_SECONDS, **kw))

    # ---------- process bookkeeping written by entrypoint.sh ----------
    def process_info(self, name: str) -> ProcessInfo:
        pid_file = self.run_dir / f"{name}.pid"
        if not pid_file.exists():
            return ProcessInfo()
        try:
            pid = int(pid_file.read_text().strip())
        except ValueError:
            return ProcessInfo()
        alive = self._pid_alive(pid)
        uptime = None
        started_file = self.run_dir / f"{name}.started"
        if alive and started_file.exists():
            try:
                uptime = max(0, int(time.time()) - int(started_file.read_text().strip()))
            except ValueError:
                uptime = None
        return ProcessInfo(pid=pid, alive=alive, uptime_seconds=uptime)

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    @property
    def supervised(self) -> bool:
        return self.run_dir.is_dir() and "SUPERVISOR_RUN_DIR" in os.environ

    # ---------- probes ----------
    def _probe_http(self, url: str, ok_statuses: range = range(200, 300), method: str = "get", **kwargs) -> ProbeResult:
        try:
            response = (self._post if method == "post" else self._get)(url, **kwargs)
        except requests.RequestException as exc:
            return ProbeResult(False, f"No answer from {url}: {exc.__class__.__name__}")
        if response.status_code in ok_statuses:
            return ProbeResult(True, f"Answering at {url}")
        return ProbeResult(False, f"{url} answered HTTP {response.status_code}")

    def _probe_engine(self, base_url: str) -> ProbeResult:
        result = self._probe_http(f"{base_url}/webui/api/service?method=get_version")
        if not result.ok:
            return result
        try:
            payload = self._get(f"{base_url}/webui/api/service?method=get_version").json()
            info = payload.get("result") or {}
            version = info.get("version")
            platform = info.get("platform")
            result.version = f"{version} ({platform})" if version and platform else version
        except Exception:  # noqa: BLE001 - version is decorative
            pass
        result.message = f"Engine answering at {base_url}"
        return result

    def _probe_ipfs_api(self, api_url: str) -> ProbeResult:
        result = self._probe_http(f"{api_url}/api/v0/version", method="post")
        if result.ok:
            try:
                result.version = self._post(f"{api_url}/api/v0/version").json().get("Version")
            except Exception:  # noqa: BLE001
                pass
            result.message = f"Kubo daemon answering at {api_url}"
        return result

    def _probe_gateway(self, gateway_url: str) -> ProbeResult:
        # The empty inline CID is served by every gateway without a network lookup.
        result = self._probe_http(f"{gateway_url}/ipfs/bafkqaaa", ok_statuses=range(200, 400))
        if result.ok:
            result.message = f"Gateway answering at {gateway_url}"
        return result

    def _probe_zeronet(self, ui_url: str) -> ProbeResult:
        result = self._probe_http(f"{ui_url}/", ok_statuses=range(200, 500))
        if result.ok:
            result.message = f"ZeroNet UI answering at {ui_url}"
        return result

    def _probe_warp(self) -> ProbeResult:
        from app.services.warp_service import WarpService

        try:
            status = asyncio.run(WarpService().get_status())
        except RuntimeError:
            # Already inside an event loop (tests); fall back to a thread.
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                status = pool.submit(lambda: asyncio.run(WarpService().get_status())).result()
        except Exception as exc:  # noqa: BLE001
            return ProbeResult(False, f"warp-cli failed: {exc}")
        if not status.get("running"):
            return ProbeResult(False, "warp-cli reports the service is not running")
        mode = status.get("mode") or "unknown"
        connected = "connected" if status.get("connected") else "disconnected"
        return ProbeResult(True, f"WARP {connected}, mode {mode}")

    # ---------- per-service evaluation ----------
    def _evaluate(self, name: str) -> Dict[str, object]:
        env = os.environ
        if name == "acestream":
            installed = _flag("IMAGE_HAS_ACESTREAM")
            enabled = _flag("ENABLE_ACESTREAM_ENGINE")
            internal = f"http://{env.get('ACESTREAM_HTTP_HOST', 'localhost')}:{env.get('ACESTREAM_HTTP_PORT', '6878')}"
            endpoint = internal if enabled else self.external_engine_url
            probe = self._probe_engine(endpoint)
            label, description = "AceStream engine", "Resolves and plays acestream:// content; used by search and status checks."
            external_possible = True
        elif name == "acexy":
            installed = _flag("IMAGE_HAS_ACEXY")
            enabled = _flag("ENABLE_ACEXY")
            endpoint = f"http://127.0.0.1:{env.get('ACEXY_STATUS_PORT', '8080')}" if (installed or enabled) else None
            probe = self._probe_http(f"{endpoint}/ace/status") if endpoint else ProbeResult(False, "Not part of this image")
            if probe.ok:
                probe.message = f"Proxying to {env.get('ACEXY_HOST', 'localhost')}:{env.get('ACEXY_PORT', '6878')}"
            label, description = "Acexy proxy", "HTTP proxy in front of the engine for players (/ace/getstream)."
            external_possible = False
        elif name == "ipfs":
            installed = _flag("IMAGE_HAS_IPFS")
            enabled = _flag("ENABLE_IPFS")
            gateway = (env.get("IPFS_GATEWAY_URL") or getattr(settings, "IPFS_GATEWAY_URL", "http://127.0.0.1:8081")).rstrip("/")
            if enabled:
                endpoint = f"http://127.0.0.1:{env.get('IPFS_API_PORT', '5001')}"
                probe = self._probe_ipfs_api(endpoint)
            else:
                endpoint = gateway
                probe = self._probe_gateway(gateway)
            label, description = "IPFS (Kubo)", "Fetches ipfs:// and ipns:// sources through an IPFS gateway."
            external_possible = True
        elif name == "zeronet":
            installed = _flag("IMAGE_HAS_ZERONET")
            enabled = _flag("ENABLE_ZERONET")
            endpoint = (env.get("ZERONET_URL") or getattr(settings, "ZERONET_URL", "http://127.0.0.1:43110")).rstrip("/")
            probe = self._probe_zeronet(endpoint)
            label, description = "ZeroNet", "Fetches zero:// sources through a ZeroNet node."
            external_possible = True
        elif name == "warp":
            installed = shutil.which("warp-cli") is not None
            enabled = _flag("ENABLE_WARP")
            endpoint = None
            probe = self._probe_warp() if installed else ProbeResult(False, "warp-cli is not installed in this image")
            label, description = "Cloudflare WARP", "Routes scraper traffic through a WARP tunnel (amd64 and arm64 images)."
            external_possible = False
        else:
            raise ServiceNotFoundError(name)

        proc = self.process_info(name)
        managed = proc.alive
        if not installed and not enabled:
            if external_possible and probe.ok:
                state, message = "external", f"Not in this image; using an external instance. {probe.message}"
            else:
                state, message = "not-installed", "Not included in this image flavor."
        elif not enabled:
            if external_possible and probe.ok:
                state, message = "external", f"Disabled here; using an external instance. {probe.message}"
            else:
                state, message = "disabled", f"Installed but turned off ({self._enable_var(name)}=false)."
        elif probe.ok:
            state, message = "running", probe.message
        elif managed:
            state, message = "unhealthy", f"Process is up but not answering. {probe.message}"
        else:
            state, message = "stopped", f"Enabled but not running. {probe.message}"

        return {
            "name": name,
            "label": label,
            "description": description,
            "state": state,
            "installed": installed,
            "enabled": enabled,
            "managed": managed,
            "running": probe.ok,
            "endpoint": endpoint,
            "version": probe.version,
            "message": message,
            "pid": proc.pid if managed else None,
            "uptime_seconds": proc.uptime_seconds if managed else None,
        }

    @staticmethod
    def _enable_var(name: str) -> str:
        return {
            "acestream": "ENABLE_ACESTREAM_ENGINE",
            "acexy": "ENABLE_ACEXY",
            "ipfs": "ENABLE_IPFS",
            "zeronet": "ENABLE_ZERONET",
            "warp": "ENABLE_WARP",
        }[name]

    def list_services(self) -> Dict[str, object]:
        return {
            "services": [self._evaluate(name) for name in SERVICE_NAMES],
            "supervised": self.supervised,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_service(self, name: str) -> Dict[str, object]:
        if name not in SERVICE_NAMES:
            raise ServiceNotFoundError(name)
        return self._evaluate(name)

    # ---------- restart ----------
    def restart(self, name: str) -> Dict[str, object]:
        if name not in SERVICE_NAMES:
            raise ServiceNotFoundError(name)
        proc = self.process_info(name)
        if not proc.alive or proc.pid is None:
            raise ServiceNotManagedError(
                f"{name} is not supervised by this container, so it cannot be restarted from here."
            )
        (self.run_dir / f"{name}.restart").write_text(datetime.now(timezone.utc).isoformat())
        self._terminate(proc.pid)
        logger.info("Restart requested for service %s (pid %s)", name, proc.pid)
        return {
            "name": name,
            "success": True,
            "message": f"Restart requested; the supervisor relaunches {name} in a moment.",
        }

    @staticmethod
    def _terminate(pid: int) -> None:
        # The entrypoint starts services with setsid, so the pid leads a process
        # group: signal the group to take the wrapper and its children together.
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            os.kill(pid, signal.SIGTERM)
