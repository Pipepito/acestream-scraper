# Accounts and casting

## First run and account recovery

On a fresh installation, open the normal application address. The first screen
explains user management and lets you create an administrator or continue without
accounts. Complete this choice before exposing a new installation to the internet:
the first person opening an unconfigured installation can configure it.

No new Docker variables, Docker secrets or setup tokens are required. Account
setup and sign-in work over HTTPS or HTTP through a private server IP on a
verified home network (for example `http://192.168.1.10:8000`). Localhost also works.
HTTP is not encrypted; use it only on a home network you trust. Internet access
still requires HTTPS, including a public address explicitly trusted for casting.
A trusted reverse proxy must preserve the real client address; a Docker gateway
alone cannot prove that a visitor is local. The setup/sign-in screen explains
when the connection cannot be verified before submitting credentials.

New passwords require 12–128 characters. Setup, account creation and password
changes show this requirement and flag invalid lengths before submission.

An existing installation keeps its previous access behavior until an operator
turns on user management in **Settings → Access**. With accounts disabled, anyone
who can reach the installation can manage it, subject to existing API-token
protection. Administrators can enable accounts later, change their own password,
create/disable accounts, set viewing permissions, revoke sessions and credentials,
or turn user management off after confirming their password.

If the owner forgets a password, run this interactive command:

```sh
docker exec -it <container> python -m app.auth reset-password
```

Enter the username and new password at the prompts. Passwords are never command
arguments or environment variables. Recovery leaves protection enabled and revokes
that account's login sessions and API credentials. Changing a password in Settings
has the same revocation behavior. There must always be an enabled administrator.

## Viewing permissions

Administrators manage the installation. Other accounts receive individual access
to Live TV, Channels, Programme guide, Events, Recordings, Playlists, Cast to my
devices, and Cast to server devices. These are viewing/casting permissions; they do
not delegate source imports, recording scheduling/deletion, integrations, settings
or diagnostics. Cast permission also needs Live TV permission to start a stream.
Recording viewers can play finished files using the existing low-priority browser
preparation; capture still takes priority. Recording casting is not supported.

The public-feature switches independently allow Live TV, Channels, Programme
guide, Events and browser casting without sign-in. Public visitors cannot view
recordings or control server TVs. Public pages use limited viewing responses,
without source URLs, headers, engine details or administrative state.

## Kodi and other IPTV players

Accounts and IPTV access are separate. Choose any of these:

- Give an account Playlists permission and create a playback-only link in its
  Playlists view. Administrators can also create a credential on the Playlist page.
- Enable public playlists, guide and media access in Settings → Access.
- Enable password-free local IPTV access and list the permitted client subnets,
  for example `192.168.1.0/24`.

Local access is evaluated from the verified client address. A private reverse
proxy, loopback address or Docker gateway alone does not establish home membership.
Forwarded client addresses are accepted only from explicitly trusted proxies.
Check the existing `FORWARDED_ALLOW_IPS` deployment option: it must identify your
actual reverse proxies, not the entire home network. A client inside a trusted
proxy range without a verified forwarded address is denied local access. For a
direct installation without a reverse proxy, `FORWARDED_ALLOW_IPS=127.0.0.1`
keeps ordinary LAN clients outside that range. This is network configuration;
account setup and password recovery do not require Docker credentials.
With user management enabled, this saved policy controls tuner access too; with
accounts disabled, the existing tuner network policy remains in force.

Protected playlists retain filters, guide IDs and optional source entries while
using the application relay. They do not export direct engine addresses, private
upstream URLs or headers. Playlist credentials travel into the guide and child
media URLs. Treat them as passwords for playback: an administrator can revoke them
in Settings → Access. After rotation, reload Kodi IPTV Simple's playlist and guide.
Administrative credentials work only in request headers, never in playback URLs.

If `API_TOKEN` was already configured, activation requires that token and explicit
confirmation that it becomes playback-only. Create replacement administrative
header credentials for scripts. The old token continues to serve existing IPTV
links; remove/rotate it when those links have been replaced. Existing installations
are never silently switched from token protection to open access.

## Cast to TVs on the server's network

1. Open **Integrations → TV casting**. On a direct home-network connection,
   casting works without accounts or manually entering TV addresses.
2. Turn on the TV. Devices appear automatically through mDNS; **Find TVs** also
   performs a bounded scan of the detected local IPv4 network when multicast is
   unavailable. A response from an ordinary web server is not a Cast receiver.
3. Open a live channel, choose **Cast…**, select a server device and start playback.

The TV uses the application address you opened in the browser, including its port
and any proxy path prefix. It must be able to fetch that address directly. Use
**Advanced connection settings → Application address for TVs** only when the TV
needs a different route. No device address is needed.

Accounts are optional for a home-only installation. When enabled, sign in using
HTTPS with Cast to server devices permission. If you use your public HTTPS address
at home, an administrator can select **I am connected to my home network now** and
**Trust this home connection**. This saves the current verified client address,
without enabling remote casting. Repeat this if your provider changes your address.
Other people sharing that public address share its network trust, but still need
account permission. Never trust a connection while away from home.

With no explicit home-network override, verified RFC1918/ULA clients are local.
An explicit **Allowed home networks** list replaces that default. A trusted proxy
must forward the real visitor address. Unresolved proxy and Docker-gateway
connections fail closed. The default proxy trust is loopback only; existing saved
proxy settings are preserved. If an older installation trusts all private ranges,
open **Set up scraper → Connection settings → Network access**, set **Trusted
reverse proxies** to the actual proxy addresses (or `127.0.0.1` without a proxy),
save, and restart. This can be changed in the app; Docker credentials are unrelated.

Android TV must provide Google Cast. Docker needs multicast connectivity for mDNS;
Linux host networking is one option. Ordinary port publishing does not forward
multicast. The fallback checks up to three detected /24 networks, at most 32
requests at once, for up to 20 seconds, with a 30-second cooldown. It accepts only
Cast identities from the fixed local device-info endpoint, including older Android
TV responses without capability information. Known audio-only devices are excluded; some TVs
block that endpoint and still require multicast. No Docker socket is used.

Cast prepares at least 20 seconds of complete HLS segments before loading the
receiver. It measures media duration because original-video segments follow the
source's keyframes and may be longer or shorter than the two-second target.
The shared player retains thirty segments, typically about one minute, to give
receivers room to buffer and resume. This increases temporary player disk usage;
the configured player-session limit still applies. Browser watching keeps its
shorter startup threshold. Both server and browser Cast use the deeper buffer.

Server casting works from Firefox and Safari as well as Chromium browsers because
the application server controls the receiver. Remote clients cannot enumerate or
control the server's TVs by default. The **Allow remote casting** switch permits
remote control only for signed-in accounts with the corresponding permission.
It never makes home TVs public.

An explicit replacement confirmation is required when a TV is already playing.
An account or local browser cannot replace another sender's app-owned cast unless
it is an administrator. Stop releases only media still owned by this app; if someone starts
something else on the receiver, cleanup does not stop that media. Playback continues
when the sender page closes or its phone locks. Stale, disconnected, revoked and
idle sessions are reclaimed. A paused server cast is released after ten minutes.
Server restart ends casting sessions; it does not restore them automatically.

Original video is the default, with AAC audio for HLS. If the receiver cannot
decode the original codec, TV casting preferences can offer compatibility conversion:
H.264/AAC, at most 720p/30 fps and one converted stream at a time. Conversion uses
CPU and is stopped when recording capture needs priority. Bundled images include
libx264; a custom FFmpeg binary must provide that encoder and the scale/fps filters.

## Cast to the visitor's own devices

**My devices** uses Google's optional Web Sender SDK, loaded only when opening the
Cast dialog. The visitor's browser presents its own device picker; the server's
home device list is not exposed. This requires HTTPS and a Cast-supported browser.
Google documents Chrome support and explicitly excludes Chrome on iOS. Firefox
and Safari can use server casting but do not provide this Web Sender path. See
[Google's Web Sender setup](https://developers.google.com/cast/docs/web_sender).

The phone/computer sends the command; the TV fetches media from the application.
It does not tunnel the video through the phone. The application address and its
certificate must therefore work from the receiver's network. Closing the sender
page does not stop an active receiver download. Receiver media URLs carry a scoped,
revocable capability, not the administrator's login or API credential.

## Backup and rollback

Keep `access.db` and `access.required` alongside the persisted application
configuration. Back them up together while the container is stopped, or use a
consistent SQLite backup procedure. They are deliberately separate from catalogue
exports and application-database recovery. Restoring or resetting the catalogue
cannot turn off account protection. A missing/corrupt access store with its
protection marker present fails closed. Restore a consistent protected backup;
do not delete the marker to work around an error.

The access store has independent Alembic migrations. Downgrading it by dropping
accounts is rejected. Before rolling back to an application version without this
feature, remove public exposure or provide equivalent reverse-proxy authentication;
older versions do not understand the new account policy. Diagnostics and image
build contexts must never contain access storage or raw credentials.
