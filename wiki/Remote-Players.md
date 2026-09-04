# Remote Players

Send a channel to VLC or Kodi somewhere else on your network — the TV in the living room, a media box, a second computer — and control it from the app: play, pause, stop, volume.

## What it does

You save each player once (name, VLC or Kodi, its address and password). After that:

- **Integrations › Remote players** lists every saved player with a live status line (Idle, or what it is playing and how far in), a play/pause button, a stop button and a volume slider.
- **Send channel…** (under "More actions for" the player) opens a picker over your TV channels and Acestream streams; pick one and it starts on that player.
- **Play on…** appears on every channel row and in the web player dialog, so you can push whatever you are looking at to a player without leaving the page.

Nothing is installed on the player. The app talks to the web interface that VLC and Kodi already ship, and hands the player a normal stream link that it opens by itself. The video never passes through your browser.

## Set up VLC

1. In VLC: **Tools › Preferences**, switch **Show settings** to **All** (bottom left).
2. Go to **Interface › Main interfaces** and tick **Web**.
3. Go to **Interface › Main interfaces › Lua**, and under **Lua HTTP** set a **Password**.
4. Restart VLC. The first time it starts, your operating system asks whether to let VLC accept network connections — **allow it**, or nothing outside that machine can reach it.

VLC's web interface listens on port **8080**. The app needs the password you set in step 3: VLC rejects every request without it, and its own error page says so in a way only VLC understands, which is why the app asks for it up front.

## Set up Kodi

1. In Kodi: **Settings › Services › Control**.
2. Turn on **Allow remote control via HTTP**.
3. Turn on **Allow remote control from applications on other systems**.
4. Set a **Username** (default `kodi`) and a **Password**.

Kodi's web interface listens on port **8080** as well. Leave the port alone unless you changed it in that same screen.

## Add a player

**Integrations › Remote players › Add player**. Fill in a name, pick **VLC** or **Kodi**, type the player's address (`192.168.1.20`, or a hostname) and its port, then the password (and username for Kodi).

Press **Test connection** before saving. It tells you in plain words what it found:

| What you see | What it means |
|---|---|
| "VLC's web interface has no password. In VLC: Tools > Preferences > All > Interface > Main interfaces > Web, then Lua > Lua HTTP > Password." | VLC answered, but its web interface is unprotected — VLC refuses commands in that state. Set the Lua HTTP password. |
| "Check the password (VLC: Lua HTTP password)." | VLC answered and rejected the password you typed. |
| "Check the Kodi username and password (Settings > Services > Control)." | Kodi answered and rejected the username/password pair. |
| "…:8080 answered, but not like VLC." | Something is on that port — a router page, a printer, another app — but it is not a player. Check the port and the player kind. |
| "Check the address and port, and that the player is running with its web interface enabled." | Nothing answered. The player is off, the address is wrong, or a firewall is in the way. |
| "This player (…) is outside TUNER_ALLOWED_NETWORKS and will get 403 from the stream link…" | The player is reachable, but it would be refused when it fetches the stream. See [Stream link format](#stream-link-format) below. |

A green result also reports the version it found, so you can tell you reached the right machine.

## Find players

Rather than hunting for addresses yourself, **Find players** checks a whole network for **port 8080** — the port both VLC and Kodi use — and lists everything that answers, each labelled VLC, Kodi or Unknown. VLC and Kodi entries get an **Add** button that opens the Add player dialog with the address, port and kind already filled in; an Unknown entry (something answers, but not like a player) is listed for information only.

The **Network** field is prefilled with a guess based on the address your browser connects from — usually right, e.g. `192.168.1.0/24`. When the app cannot guess it, the field starts empty and the hint asks you to type it. That happens on **Docker Desktop** (macOS and Windows), where every request reaches the container from Docker's own gateway rather than from your real address: type your LAN's network, for example `192.168.1.0/24`.

Rules the scan enforces, so it stays a local convenience and never a port scanner pointed at the internet:

- The network must be a private one: `10.0.0.0/8`, `100.64.0.0/10`, `172.16.0.0/12`, `192.168.0.0/16` or `fc00::/7`. Anything else is refused: "Only private networks can be scanned (10/8, 100.64/10, 172.16/12, 192.168/16, fc00::/7)".
- At most **1024** addresses — a `/22` or smaller for IPv4. A larger range is refused ("Scan at most 1024 addresses at a time"); scan one subnet at a time.

A `/24` typically finishes in a few seconds. If nothing answers, the dialog says so and points you back at the VLC and Kodi setup steps above — the usual cause is a web interface that was never switched on, or a firewall prompt that was dismissed.

## Stream link format

Each player has a **Stream link format**, chosen when you add or edit it. It decides which address the player is told to open.

- **Server relay (recommended)** — the default. The player fetches `http://<this server>/tuner/stream/<id>.ts` and the app relays the stream to it. It works with every image flavor and with an external engine, and only **port 8000** (the app itself) has to be reachable from the player. The cost is that the stream passes through this server.
- **A named stream base URL** (Settings › Stream base URLs) — the player is handed an Acexy or engine link instead and fetches the stream directly. That is less work for this server, but the player must be able to reach **that** address: publish the Acexy port (`8080`) or the engine port (`6878`) from the container, and make sure the base URL names an address the player can resolve — not `localhost`, which on the player means the player itself.

The relay route is gated by network address rather than by the API token, because VLC and Kodi cannot send one. `TUNER_ALLOWED_NETWORKS` (see [Configuration Reference](Configuration.md#media-integrations)) lists who may fetch it; its default covers every private range, so a player on your LAN works with no configuration. **Test connection** checks the player's address against that list and warns you before you save if it would be refused.

`PUBLIC_BASE_URL` decides which address the app puts in the link. Leave it empty and the app derives it per request; set it when the app sits behind a reverse proxy or when players reach it on a different name than your browser does.

### Tailscale

A player reachable over Tailscale works out of the box: Tailscale addresses are in `100.64.0.0/10`, which is both in the default `TUNER_ALLOWED_NETWORKS` and in the ranges **Find players** will scan. Set `PUBLIC_BASE_URL` to this server's Tailscale address (for example `http://100.101.102.103:8000`) so the link handed to the player points at an address it can reach.

## Errors while playing

If a player stops answering, its card says "The player did not answer. Is it running with its web interface on?" and the transport buttons stop working until it comes back. Sending a channel to a player that has lost its password shows the same guided password message as **Test connection** — the app never confuses a player's password with the app's own `API_TOKEN`.

Seeking is deliberately absent. These are live streams, and VLC and Kodi disagree about what a seek means on one.

## About the passwords

**Player passwords are stored unencrypted in the app's database** (`config/scraper.db`), the same way the app stores its other settings. They are never returned by the API (it only reports whether a password is set) and never written to the logs, but anyone who can read the database file can read them.

A saved password belongs to one address: **change a player's address or port and the saved password is cleared**, so type it again in the same edit. A player at a new address is a new device, and the app will not send the old one's password to it.

That is a deliberate trade-off for a single-user app with no key management: treat the database file as a secret, keep the app off untrusted networks, and use passwords you do not reuse elsewhere. See [Reverse Proxy / HTTPS](https://github.com/Pipepito/acestream-scraper/blob/main/docs/ops/reverse-proxy.md) if you expose the app beyond a trusted network.

## See also

- [Web Player](Web-Player.md) — play a channel in the browser instead
- [Configuration Reference](Configuration.md#media-integrations) — `TUNER_ALLOWED_NETWORKS`, `PUBLIC_BASE_URL` and the rest
