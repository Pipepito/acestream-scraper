"""Share Android's fixed DNS socket across bundled engine processes.

The upstream listener removes its socket in finally, including after a failed
bind. A second engine must therefore never call it while another owns the path.
The lock stays open for the lifetime of the listener. When its engine exits,
the other engine's waiting thread takes over and removes the stale socket.
"""
import fcntl
import os
import threading
import time


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
