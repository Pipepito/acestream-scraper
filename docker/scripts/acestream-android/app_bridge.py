# Linux replacement for the Android engine's app_bridge.py (SL4A-style RPC
# client; original Copyright 2009 Google Inc., Apache License 2.0, author
# Damon Kohler). On Android the engine asks the host app for ~30 device facts
# over JSON-RPC (AP_HOST/AP_PORT); the stock fallback answers six of them and
# hard-codes /sdcard/org.acestream.engine. This version keeps the real RPC
# path intact and makes the fake host Linux-aware: configurable home dir
# (ACESTREAM_HOME), statvfs/meminfo-backed disk and memory answers and a
# persistent per-install device id.
import collections
import hashlib
import json
import os
import platform
import socket
import uuid

PORT = os.environ.get("AP_PORT")
HOST = os.environ.get("AP_HOST")
HANDSHAKE = os.environ.get("AP_HANDSHAKE")
Result = collections.namedtuple("Result", "id,result,error")
_HOME = os.environ.get("ACESTREAM_HOME", "/var/lib/acestream")
_ENGINE_VERSION = "3.1.80"
_ENGINE_VERSION_CODE = "3018000"
_ABI_BY_MACHINE = {"aarch64": "arm64-v8a", "armv7l": "armeabi-v7a", "armv8l": "armeabi-v7a"}


def _meminfo(key):
    try:
        with open("/proc/meminfo") as handle:
            for line in handle:
                if line.startswith(key + ":"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    return 1024 * 1024 * 1024


_DEVICE_ID = None


def _device_id():
    """Persistent per-install id (ACESTREAM_HOME/.device_id); stable within a
    process even when the home dir is not writable."""
    global _DEVICE_ID
    if _DEVICE_ID:
        return _DEVICE_ID
    path = os.path.join(_HOME, ".device_id")
    try:
        with open(path) as handle:
            value = handle.read().strip()
    except Exception:
        value = ""
    if not value:
        value = str(uuid.uuid4())
        try:
            os.makedirs(_HOME, exist_ok=True)
            with open(path, "w") as handle:
                handle.write(value)
        except Exception:
            pass
    _DEVICE_ID = value
    return value


def _statvfs(path):
    try:
        return os.statvfs(path if path and os.path.exists(path) else _HOME)
    except Exception:
        return None


class Android(object):
    def __init__(self, addr=None):
        self.use_fake_host = False
        if addr is None:
            if HOST is None:
                self.use_fake_host = True
            else:
                addr = HOST, PORT
        if not self.use_fake_host:
            self.conn = socket.create_connection(addr)
            self.client = self.conn.makefile(mode="rw")
            self.id = 0
            if HANDSHAKE is not None:
                self._authenticate(HANDSHAKE)

    def _rpc(self, method, *args):
        request = json.dumps({"id": self.id, "method": method, "params": args})
        self.client.write(request + "\n")
        self.client.flush()
        response = self.client.readline()
        self.id += 1
        result = json.loads(response)
        if result["error"] is not None:
            print(result["error"])
        return result["result"]

    def _fake_rpc(self, method, *args):
        machine = platform.machine()
        if method == "getAceStreamHome":
            return _HOME
        if method == "makeToast":
            print(args[0] if args else "")
            return None
        if method == "getDisplayLanguage":
            return "en"
        if method == "getLocale":
            return "en-US"
        if method in ("getRAMSize", "getMaxMemory"):
            return _meminfo("MemTotal")
        if method == "getMemoryClass":
            return 256
        if method in ("getDeviceId", "getAppId", "getDeviceUuidString"):
            return _device_id()
        if method == "getDeviceManufacturer":
            return "Linux"
        if method == "getDeviceModel":
            return machine
        if method == "getDeviceName":
            return "Linux " + machine
        if method == "getDeviceProductName":
            return "linux"
        if method in ("getArch", "getDeviceABI"):
            return _ABI_BY_MACHINE.get(machine, machine)
        if method == "getAppVersionCode":
            return _ENGINE_VERSION_CODE
        if method == "getVersion":
            return _ENGINE_VERSION
        if method == "getPackageName":
            return "org.acestream.core"
        if method == "getUserAgent":
            return "AceStream/%s (Linux; %s)" % (_ENGINE_VERSION, machine)
        if method in ("isAndroidTv", "hasBrowser", "hasWebView"):
            return False
        if method == "isConnectable":
            return True
        if method == "getAppInfo":
            return json.dumps(
                {
                    "appId": _device_id(),
                    "appVersionCode": _ENGINE_VERSION_CODE,
                    "deviceId": _device_id(),
                    "arch": machine,
                    "locale": "en-US",
                    "isAndroidTv": False,
                    "hasBrowser": False,
                    "hasWebView": False,
                }
            )
        if method in (
            "getAvailableBlocks",
            "getBlockCount",
            "getBlockSize",
            "getAvailableBytes",
            "getFreeBytes",
            "getTotalBytes",
        ):
            st = _statvfs(args[0] if args else None)
            if st is None:
                return 0
            return {
                "getAvailableBlocks": st.f_bavail,
                "getBlockCount": st.f_blocks,
                "getBlockSize": st.f_frsize,
                "getAvailableBytes": st.f_bavail * st.f_frsize,
                "getFreeBytes": st.f_bfree * st.f_frsize,
                "getTotalBytes": st.f_blocks * st.f_frsize,
            }[method]
        if method in (
            "onSettingsUpdated",
            "onEvent",
            "onAuthUpdated",
            "showNotification",
            "publishFileReceiverState",
            "adjustCacheSettings",
        ):
            return None
        print("app_bridge(fake): unhandled RPC %s%r -> None" % (method, args))
        return None

    def __getattr__(self, name):
        def rpc_call(*args):
            if self.use_fake_host:
                return self._fake_rpc(name, *args)
            return self._rpc(name, *args)

        return rpc_call
