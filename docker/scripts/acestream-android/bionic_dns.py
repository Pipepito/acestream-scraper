"""Share Android's fixed DNS socket across bundled engine processes.

The upstream listener removes its socket in finally, including after a failed
bind. A second engine must therefore never call it while another owns the path.
The lock stays open for the lifetime of the listener. When its engine exits,
the other engine's waiting thread takes over and removes the stale socket.
"""
import fcntl
import ipaddress
import os
import threading
import time


def container_resolver(resolver_type, log, path="/etc/resolv.conf"):
    """Follow Docker/WARP resolver changes without restarting either engine.

    Keep the last valid servers during a partial rewrite. Refresh before DNS
    work, not on a timer, so reconnects also work after a long idle period.
    """
    class ReloadingResolver(resolver_type):
        def __init__(self):
            super().__init__(configure=False)
            self._configuration_lock = threading.Lock()
            self._configuration_error = None
            self._refresh(required=True)

        def _refresh(self, required=False):
            with self._configuration_lock:
                try:
                    with open(path) as handle:
                        content = handle.read(65537)
                    if len(content) > 65536:
                        raise ValueError("resolver configuration exceeds 64 KiB")
                    servers = []
                    for line in content.splitlines():
                        fields = line.split("#", 1)[0].split()
                        if len(fields) == 2 and fields[0] == "nameserver":
                            ipaddress.ip_address(fields[1])
                            if fields[1] not in servers:
                                servers.append(fields[1])
                    if not servers:
                        raise ValueError("no nameservers configured")
                    if list(self.nameservers) != servers:
                        self.nameservers = servers
                        log("bionic DNS resolver configuration updated")
                    self._configuration_error = None
                except (OSError, ValueError) as exc:
                    if required:
                        raise
                    error = type(exc).__name__
                    if self._configuration_error != error:
                        log("bionic DNS configuration unavailable; retaining last valid servers")
                        self._configuration_error = error

        def resolve(self, *args, **kwargs):
            self._refresh()
            return super().resolve(*args, **kwargs)

    return ReloadingResolver()


def run_shared_listener(listener, resolver, socket_path="/dev/socket/dnsproxyd"):
    os.makedirs(os.path.dirname(socket_path), exist_ok=True)
    while True:
        try:
            # Never unlink the lock file: all engines must lock the same inode.
            with open(socket_path + ".lock", "a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    os.unlink(socket_path)
                except FileNotFoundError:
                    pass
                listener(resolver)
        except Exception as exc:
            print("bionic DNS listener failed; retrying: {}".format(exc), flush=True)
        time.sleep(1)


def start_shared_dns(listener, resolver):
    thread = threading.Thread(
        target=run_shared_listener, args=(listener, resolver),
        name="shared-dnsproxyd", daemon=True,
    )
    thread.start()
    return thread
