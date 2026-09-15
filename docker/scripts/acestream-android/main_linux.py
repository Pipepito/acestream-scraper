"""Linux bootstrap for the Android AceStream engine payload.

Mirrors the APK's ``main.py`` (RPC host, home dir, ``acestream.conf`` tokens,
``--client-console``) without redirecting stdout/stderr into
``acestream_std.log``, so ``--log-stdout`` output reaches ``docker logs``.
OCI distributions must enter through their packaged ``aceserve.main()``;
calling Core.run directly skips distribution initialization and can reject
playback with mod_detected even though health/version requests succeed.
Legacy APK payloads retain their original Core.run entry point.
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


def configure_bionic_dns():
    """Route Python/socket lookups through Docker's resolv.conf.

    The jopsis 3.2.17 distribution includes dnsproxyd for this purpose because
    Android bionic does not use glibc's resolver configuration directly.
    Older official APK payloads do not include the helper and simply retain
    their existing behavior.
    """
    try:
        import dns.resolver
        from dnsproxyd import dnsproxyd_listener
        from bionic_dns import container_resolver, start_shared_dns

        resolver = container_resolver(dns.resolver.Resolver, log)
        dns.resolver.override_system_resolver(resolver)
        start_shared_dns(dnsproxyd_listener, resolver)
        log("bionic DNS resolver configured")
    except Exception as exc:
        log("bionic DNS resolver unavailable: {}".format(exc))


try:
    log("linux bootstrap; home {}".format(home_dir))
    configure_bionic_dns()
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
    # The installer preserves this file only for the pinned OCI distribution.
    # Do not fall back to Core if its packaged entry point fails: that can
    # produce a healthy API with broken playback and hide installation errors.
    if os.path.isfile(os.path.join(os.path.dirname(__file__), "main.py.oci-orig")):
        import aceserve

        sys.argv = params
        aceserve.main()
    else:
        from acestreamengine import Core

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
