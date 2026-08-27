"""Linux bootstrap for the Android AceStream engine payload.

Mirrors the APK's ``main.py`` (RPC host, home dir, ``acestream.conf`` tokens,
``--client-console``) without redirecting stdout/stderr into
``acestream_std.log``, so ``--log-stdout`` output reaches ``docker logs``.
Launched by ``start-engine`` with the bionic CPython 3.8 from the payload.
"""
import os
import sys
import threading
import traceback
from datetime import datetime

import app_bridge

droid = app_bridge.Android()
home_dir = droid.getAceStreamHome()
os.makedirs(home_dir, exist_ok=True)


def log(msg):
    try:
        with open(os.path.join(home_dir, "acestream.log"), "a") as handle:
            handle.write(
                "{}|{}|bootstrap|{}\n".format(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    threading.current_thread().name,
                    msg,
                )
            )
    except Exception:
        pass


try:
    log("linux bootstrap; home {}".format(home_dir))
    from acestreamengine import Core

    conf_file = os.path.join(home_dir, "acestream.conf")
    parsed_params = []
    if os.path.isfile(conf_file):
        import argparse

        parser = argparse.ArgumentParser(prog="acestream", fromfile_prefix_chars="@")
        try:
            _, parsed_params = parser.parse_known_args(["@" + conf_file])
        except Exception as exc:  # noqa: BLE001 - engine keeps defaults
            log("failed to load conf file: {}".format(exc))

    params = sys.argv[:]
    if "--client-console" not in params:
        params.append("--client-console")
    params.extend(parsed_params)
    Core.run(params)
except Exception as exc:  # noqa: BLE001 - surface and exit non-zero
    log("Got error on start: {}".format(exc))
    try:
        with open(os.path.join(home_dir, "acestream_error.log"), "a") as handle:
            traceback.print_exc(file=handle)
    except Exception:
        pass
    traceback.print_exc()
    sys.exit(1)
