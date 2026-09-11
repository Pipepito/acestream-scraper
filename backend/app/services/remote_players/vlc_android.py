"""VLC Android 3.6 Remote access (HTTPS, OTP and user_session cookie).

Protocol reference: VideoLAN/vlc-android tag 3.6.5, RemoteAccessRouting.kt,
RemoteAccessOTP.kt and websockets/WSIncomingMessage.kt. Not the desktop Lua API.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import socket
import ssl
from contextlib import contextmanager
from typing import Iterator, Optional

import httpx

from .base import (
    DRIVER_TIMEOUT, PlayerAuthError, PlayerCommandError, PlayerProbe, PlayerStatus,
    PlayerUnreachable, guard,
)

PAIR_HINT = "Pair VLC Android again in Integrations > Remote players > Edit."


def certificate_context(host: str, port: int, fingerprint: Optional[str]) -> tuple[ssl.SSLContext, str]:
    """Inspect without credentials, then trust only this exact device certificate.

    Initial pairing is trust on first use; subsequent calls check the saved pin
    before sending a cookie or code. The actual HTTP connection verifies TLS
    against that certificate, including across DNS changes between connections.
    """
    guard(host)
    bare = host.strip("[]")
    inspection = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    inspection.check_hostname = False
    inspection.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((bare, port), timeout=2) as tcp:
            with inspection.wrap_socket(tcp, server_hostname=bare) as tls:
                cert = tls.getpeercert(binary_form=True)
        if not cert:
            raise PlayerUnreachable("VLC Android did not provide a certificate.")
        actual = hashlib.sha256(cert).hexdigest()
        if fingerprint and not hmac.compare_digest(actual, fingerprint):
            raise PlayerAuthError("pairing_required", "VLC Android's certificate changed. " + PAIR_HINT)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False  # VLC's self-signed certificate does not name its LAN IP.
        context.load_verify_locations(cadata=ssl.DER_cert_to_PEM_cert(cert))
        return context, actual
    except (OSError, ValueError) as exc:
        raise PlayerUnreachable("Cannot reach VLC Android over HTTPS. Check its Remote access address and secure port.") from exc


@contextmanager
def secure_client(host: str, port: int, fingerprint: Optional[str]) -> Iterator[tuple[httpx.Client, str]]:
    context, actual = certificate_context(host, port, fingerprint)
    guard(host)
    with httpx.Client(verify=context, follow_redirects=False, timeout=DRIVER_TIMEOUT, trust_env=False) as client:
        yield client, actual


def request(client: httpx.Client, host: str, port: int, method: str, path: str, **kwargs) -> httpx.Response:
    guard(host)
    try:
        response = client.request(method, f"https://{host}:{port}{path}", **kwargs)
    except httpx.HTTPError as exc:
        raise PlayerUnreachable("VLC Android did not answer. Check that Remote access is running.") from exc
    if response.status_code == 401:
        raise PlayerAuthError("pairing_required", PAIR_HINT)
    if response.status_code == 403:
        raise PlayerCommandError("Enable playback control in VLC Android's Remote access settings and keep VLC in the foreground to open video.")
    if response.status_code == 429:
        raise PlayerCommandError("VLC Android rejected too many pairing attempts. Wait before requesting a new code.")
    if response.status_code >= 400:
        raise PlayerCommandError(f"VLC Android answered HTTP {response.status_code}.")
    if 300 <= response.status_code < 400 and path != "/verify-code":
        raise PlayerCommandError("VLC Android redirected the request. Check its HTTPS port or pair again.")
    return response


def start_pairing(host: str, port: int) -> dict[str, str]:
    with secure_client(host, port, None) as (client, fingerprint):
        response = request(client, host, port, "POST", "/code", data={})
        challenge = response.text.strip()
        if not challenge or len(challenge) > 256 or "<" in challenge:
            raise PlayerCommandError("This is not a VLC Android pairing service.")
        return {"challenge": challenge, "fingerprint": fingerprint}


def finish_pairing(host: str, port: int, challenge: str, fingerprint: str, code: str) -> str:
    with secure_client(host, port, fingerprint) as (client, _):
        digest = hashlib.sha256((code + challenge).encode()).hexdigest()
        response = request(client, host, port, "POST", "/verify-code", data={"code": digest})
        session = response.cookies.get("user_session")
        if response.status_code != 302 or response.headers.get("location") != "/" or not session:
            raise PlayerAuthError("pairing_required", "The code is incorrect or expired. Request a new code and enter it within 60 seconds.")
        credential = json.dumps({"host": host.lower(), "port": port, "fingerprint": fingerprint, "session": session}, separators=(",", ":"))
        if len(credential) > 1024:
            raise PlayerCommandError("VLC Android returned an unsupported session size.")
        return credential


class VlcAndroidDriver:
    def __init__(self, host: str, port: int, password: Optional[str]):
        self.host, self.port, self.password = host, int(port), password

    def _credentials(self) -> dict:
        try:
            data = json.loads(self.password or "{}")
            if (not isinstance(data, dict) or data.get("host") != self.host.lower()
                    or data.get("port") != self.port or not isinstance(data.get("session"), str)
                    or not data["session"] or not isinstance(data.get("fingerprint"), str)
                    or re.fullmatch(r"[0-9a-f]{64}", data["fingerprint"]) is None
                    or re.fullmatch(r'[!#-:<-~]+', data["session"]) is None):
                raise ValueError
            return data
        except (ValueError, TypeError):
            raise PlayerAuthError("pairing_required", PAIR_HINT) from None

    @contextmanager
    def _client(self) -> Iterator[httpx.Client]:
        credentials = self._credentials()
        with secure_client(self.host, self.port, credentials["fingerprint"]) as (client, _):
            # A request-specific header avoids accepting cookies for unrelated domains.
            client.headers["Cookie"] = f"user_session={credentials['session']}"
            yield client

    def _event(self, message: str, **params) -> None:
        with self._client() as client:
            request(client, self.host, self.port, "GET", "/playback-event", params={"message": message, **params})

    def probe(self) -> PlayerProbe:
        try:
            self._event("hello")  # Recognized, read-only, does not require playback permission.
        except PlayerAuthError as exc:
            return PlayerProbe(bool(self.password), False, None, str(exc), str(exc))
        return PlayerProbe(True, True, None, "VLC Android is paired.")

    def status(self) -> PlayerStatus:
        with self._client() as client:
            # A first response can drain unrelated events from VLC's shared queue.
            for _ in range(2):
                response = request(client, self.host, self.port, "GET", "/longpolling")
                try:
                    messages = response.json()
                    if not isinstance(messages, list) or any(not isinstance(m, dict) for m in messages):
                        raise ValueError
                    current = next((m for m in reversed(messages) if m.get("type") == "now-playing"), None)
                    if current is not None:
                        return PlayerStatus(
                            state="playing" if current["playing"] else "paused",
                            title=current.get("title"),
                            position_s=max(0, int(current.get("progress", 0)) // 1000),
                            length_s=max(0, int(current.get("duration", 0)) // 1000) or None,
                            volume_pct=max(0, min(100, int(current.get("volume", 0)))),
                        )
                    if any(m.get("type") == "player-status" and m.get("playing") is False for m in messages):
                        return PlayerStatus(state="stopped")
                except (ValueError, TypeError, KeyError) as exc:
                    raise PlayerCommandError("VLC Android returned an invalid playback status.") from exc
        raise PlayerCommandError("VLC Android has not provided playback status yet. Try again.")

    def play(self, url: str, title: str) -> None:
        with self._client() as client:
            request(client, self.host, self.port, "GET", "/play", params={"id": "0", "path": url, "append": "false"})

    def pause(self) -> None:
        self._event("pause")

    def resume(self) -> None:
        self._event("play")

    def stop(self) -> None:
        raise PlayerCommandError("VLC Android Remote access does not expose Stop. Use Pause or stop playback on the device.")

    def set_volume(self, pct: int) -> None:
        self._event("set-volume", id=max(0, min(100, int(pct))))
