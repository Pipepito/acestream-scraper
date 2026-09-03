/* AceStream Scraper — Docker command builder.
 *
 * Facts (flavors, ports, volumes, notes) come from builder/runtime-options.json.
 * This file holds the wiring: which options appear for which choices, and how
 * the docker run / compose output is assembled. When the runtime contract
 * changes, edit the JSON first; touch this file only when a *rule* changes
 * (e.g. a new feature toggle or a new dependency between options).
 */
(function () {
  'use strict';

  const $ = (sel) => document.querySelector(sel);
  const el = (tag, attrs = {}, children = []) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key === 'html') node.innerHTML = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else if (value === true) node.setAttribute(key, '');
      else if (value !== false && value != null) node.setAttribute(key, value);
    }
    for (const child of children) if (child) node.append(child);
    return node;
  };

  const CHANNELS = [
    { id: 'release', label: 'Latest release', hint: 'recommended' },
    { id: 'develop', label: 'Pre-release (develop)', hint: 'for testing' },
    { id: 'version', label: 'Specific version', hint: '' }
  ];

  let data = null;

  const state = {
    flavor: null,
    platform: 'amd64',
    channel: 'release',
    version: '',
    engine: true,
    acexy: true,
    warp: false,
    zeronet: false,
    zeronetEmbedded: true,
    zeronetUrl: '',
    ipfs: false,
    ipfsEmbedded: true,
    ipfsGatewayUrl: '',
    extEngineHost: '',
    extEnginePort: 6878,
    ports: {},    // id -> { enabled, host }
    volumes: {},  // id -> { enabled, source }
    containerName: 'acestream-scraper',
    restart: 'unless-stopped',
    tz: '',
    publicBaseUrl: '',
    tunerNetworks: '',
    playerMaxSessions: ''
  };

  // ---------------------------------------------------------------------------
  // Derived facts about the current selection.
  // ---------------------------------------------------------------------------
  function derive() {
    const flavor = data.flavors.find((f) => f.id === state.flavor) || data.flavors[0];
    const platform = data.platforms.find((p) => p.id === state.platform) || data.platforms[0];
    const imageHasEngine = flavor.features.includes('acestream');
    const imageHasAcexy = flavor.features.includes('acexy');
    const engineOn = imageHasEngine && state.engine;
    const acexyOn = imageHasAcexy && state.acexy;
    const warpOn = platform.warpAvailable && state.warp;
    const needsExternalEngine = acexyOn && !engineOn;
    const ipfsEmbeddedOn = state.ipfs && state.ipfsEmbedded && platform.ipfsAvailable;
    const ipfsExternalOn = state.ipfs && !ipfsEmbeddedOn;
    const zeronetEmbeddedOn = state.zeronet && state.zeronetEmbedded && platform.zeronetAvailable;
    const zeronetExternalOn = state.zeronet && !zeronetEmbeddedOn;

    const activePorts = data.ports.filter((p) => {
      if (p.id === 'web') return true;
      if (p.id === 'acexy') return acexyOn;
      if (p.id === 'engineApi' || p.id === 'p2p') return engineOn;
      if (p.id === 'ipfsSwarm' || p.id === 'ipfsGateway') return ipfsEmbeddedOn;
      if (p.id === 'zeronetUi' || p.id === 'zeronetFileserver') return zeronetEmbeddedOn;
      return false;
    });
    const activeVolumes = data.volumes.filter((v) => {
      if (v.id === 'config') return true;
      if (v.id === 'engineState') return engineOn;
      if (v.id === 'ipfsRepo') return ipfsEmbeddedOn;
      if (v.id === 'zeronetData') return zeronetEmbeddedOn;
      return false;
    });

    return { flavor, platform, imageHasEngine, imageHasAcexy, engineOn, acexyOn, warpOn, needsExternalEngine, ipfsEmbeddedOn, ipfsExternalOn, zeronetEmbeddedOn, zeronetExternalOn, activePorts, activeVolumes };
  }

  function imageTag(flavor) {
    if (state.channel === 'develop') return flavor.developTag;
    if (state.channel === 'version') {
      let v = state.version.trim();
      if (!v) return flavor.versionTagPattern;
      if (/^\d/.test(v)) v = 'v' + v;
      return flavor.versionTagPattern.replace('vX.Y.Z', v);
    }
    return flavor.releaseTag;
  }

  function validPort(value) {
    const n = Number(value);
    return Number.isInteger(n) && n >= 1 && n <= 65535 ? n : null;
  }

  function safeName(name) {
    return /^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/.test(name) ? name : null;
  }

  // ---------------------------------------------------------------------------
  // Output assembly.
  // ---------------------------------------------------------------------------
  function envEntries(d) {
    const env = [];
    if (d.engineOn) env.push(['ENABLE_ACESTREAM_ENGINE', 'true']);
    if (d.acexyOn) env.push(['ENABLE_ACEXY', 'true']);
    if (d.needsExternalEngine) {
      env.push(['ACEXY_HOST', state.extEngineHost.trim() || '<engine-host>']);
      env.push(['ACEXY_PORT', String(validPort(state.extEnginePort) || 6878)]);
    }
    if (d.warpOn) {
      env.push(['ENABLE_WARP', 'true']);
      env.push(['WARP_ENABLE_NAT', 'true']);
    }
    if (d.zeronetEmbeddedOn) env.push(['ENABLE_ZERONET', 'true']);
    if (d.zeronetExternalOn) env.push(['ZERONET_URL', state.zeronetUrl.trim() || data.zeronet.defaultUrl]);
    if (d.ipfsEmbeddedOn) env.push(['ENABLE_IPFS', 'true']);
    if (d.ipfsExternalOn) env.push(['IPFS_GATEWAY_URL', state.ipfsGatewayUrl.trim() || data.ipfs.defaultGatewayUrl]);
    if (state.tz.trim()) env.push(['TZ', state.tz.trim()]);
    if (state.publicBaseUrl.trim()) env.push(['PUBLIC_BASE_URL', state.publicBaseUrl.trim()]);
    if (state.tunerNetworks.trim()) env.push(['TUNER_ALLOWED_NETWORKS', state.tunerNetworks.trim()]);
    if (/^\d+$/.test(state.playerMaxSessions.trim())) env.push(['PLAYER_MAX_SESSIONS', state.playerMaxSessions.trim()]);
    return env;
  }

  function portEntries(d) {
    const out = [];
    for (const p of d.activePorts) {
      const s = state.ports[p.id];
      if (!s || !s.enabled) continue;
      const host = validPort(s.host) || p.defaultHost;
      for (const proto of p.protocols) {
        // hostAddress pins a mapping to one host address. The web port uses it
        // (see runtime-options.json): an unaddressed publish also listens on
        // [::], and docker-proxy then rewrites every IPv6 client to the bridge
        // gateway, which defeats the tuner routes' network check.
        out.push({ address: p.hostAddress ? p.hostAddress + ':' : '', host, container: p.container, proto, label: p.label });
      }
    }
    return out;
  }

  function volumeEntries(d) {
    const out = [];
    for (const v of d.activeVolumes) {
      const s = state.volumes[v.id];
      if (!s || !s.enabled) continue;
      const source = (s.source || '').trim() || v.defaultSource;
      out.push({ source, target: v.target, label: v.label });
    }
    return out;
  }

  function usesHostGateway(d) {
    if (d.zeronetExternalOn && (state.zeronetUrl.trim() || data.zeronet.defaultUrl).includes('host.docker.internal')) return true;
    return d.ipfsExternalOn && (state.ipfsGatewayUrl.trim() || data.ipfs.defaultGatewayUrl).includes('host.docker.internal');
  }

  function runVolumeFlag(source, target) {
    // docker run needs an absolute path for bind mounts (quoted, like the wiki
    // examples); named volumes are passed through as-is.
    if (source.startsWith('./')) return `"\${PWD}/${source.slice(2)}:${target}"`;
    if (source === '.') return `"\${PWD}:${target}"`;
    if (source.startsWith('/') || source.startsWith('~')) return `"${source}:${target}"`;
    return `${source}:${target}`;
  }

  function buildRunCommand(d) {
    const image = `${data.image}:${imageTag(d.flavor)}`;
    const lines = [`docker pull ${image}`, '', 'docker run -d \\'];
    const name = safeName(state.containerName.trim()) || 'acestream-scraper';
    lines.push(`  --name ${name} \\`);
    if (state.restart !== 'no') lines.push(`  --restart ${state.restart} \\`);
    if (d.warpOn) {
      lines.push('  --cap-add NET_ADMIN \\');
      lines.push('  --cap-add SYS_ADMIN \\');
      lines.push('  --device /dev/net/tun:/dev/net/tun \\');
    }
    if (usesHostGateway(d)) lines.push('  --add-host host.docker.internal:host-gateway \\');
    for (const [k, v] of envEntries(d)) lines.push(`  -e ${k}=${v} \\`);
    for (const p of portEntries(d)) {
      const suffix = p.proto === 'udp' ? '/udp' : '';
      lines.push(`  -p ${p.address}${p.host}:${p.container}${suffix} \\`);
    }
    for (const v of volumeEntries(d)) lines.push(`  -v ${runVolumeFlag(v.source, v.target)} \\`);
    lines.push(`  ${image}`);
    return lines.join('\n');
  }

  function buildCompose(d) {
    const image = `${data.image}:${imageTag(d.flavor)}`;
    const name = safeName(state.containerName.trim()) || 'acestream-scraper';
    const lines = ['services:', `  ${name}:`, `    image: ${image}`, `    container_name: ${name}`];
    if (state.restart !== 'no') lines.push(`    restart: ${state.restart}`);

    const ports = portEntries(d);
    if (ports.length) {
      lines.push('    ports:');
      for (const p of ports) {
        const suffix = p.proto === 'udp' ? '/udp' : '';
        const mapping = `"${p.address}${p.host}:${p.container}${suffix}"`;
        lines.push(`      - ${mapping.padEnd(20)} # ${p.label}${p.proto === 'udp' ? ' (UDP)' : ''}`);
      }
    }

    const env = [];
    // Compose documents intent: list every toggle the image knows about explicitly.
    if (d.imageHasEngine) env.push(['ENABLE_ACESTREAM_ENGINE', d.engineOn ? 'true' : 'false']);
    if (d.imageHasAcexy) env.push(['ENABLE_ACEXY', d.acexyOn ? 'true' : 'false']);
    if (d.platform.warpAvailable) env.push(['ENABLE_WARP', d.warpOn ? 'true' : 'false']);
    if (d.platform.zeronetAvailable) env.push(['ENABLE_ZERONET', d.zeronetEmbeddedOn ? 'true' : 'false']);
    if (d.platform.ipfsAvailable) env.push(['ENABLE_IPFS', d.ipfsEmbeddedOn ? 'true' : 'false']);
    for (const [k, v] of envEntries(d)) {
      if (!env.some((e) => e[0] === k)) env.push([k, v]);
    }
    if (env.length) {
      lines.push('    environment:');
      for (const [k, v] of env) lines.push(`      - ${k}=${v}`);
    }

    const volumes = volumeEntries(d);
    if (volumes.length) {
      lines.push('    volumes:');
      for (const v of volumes) lines.push(`      - ${v.source}:${v.target}`);
    }
    if (d.warpOn) {
      lines.push('    cap_add:');
      lines.push('      - NET_ADMIN');
      lines.push('      - SYS_ADMIN');
      lines.push('    devices:');
      lines.push('      - /dev/net/tun:/dev/net/tun');
    }
    if (usesHostGateway(d)) {
      lines.push('    extra_hosts:');
      lines.push('      - "host.docker.internal:host-gateway"');
    }
    const named = volumes.filter((v) => !/^[./~]/.test(v.source));
    if (named.length) {
      lines.push('');
      lines.push('volumes:');
      for (const v of named) lines.push(`  ${v.source}:`);
    }
    return lines.join('\n');
  }

  function collectWarnings(d) {
    const notes = data.notes;
    const out = [];
    if (state.channel === 'develop') out.push(['info', notes.developChannel]);
    if (state.channel === 'version' && !state.version.trim()) {
      out.push(['error', 'Enter the version to pin (for example v2.0.0). Release tags are listed on Docker Hub.']);
    }
    if (!d.imageHasEngine) {
      out.push(['info', 'This flavor has no AceStream engine. ' + notes.externalEngineSettings]);
    } else if (!d.engineOn) {
      out.push(['info', 'The engine is installed but will not start. ' + notes.externalEngineSettings]);
    }
    if (d.needsExternalEngine) {
      const host = state.extEngineHost.trim();
      if (!host || /^(localhost|127\.0\.0\.1)$/i.test(host)) {
        out.push(['error', 'Enter the address of your external AceStream engine. ' + notes.acexyExternalEngine]);
      }
    }
    if (d.engineOn && d.platform.id === 'armv7') out.push(['warn', notes.armv7Experimental]);
    if (d.engineOn && d.platform.id !== 'amd64') out.push(['info', notes.armPageSize]);
    if (state.warp && !d.platform.warpAvailable) out.push(['warn', 'WARP is switched off for this platform. ' + notes.warpArm]);
    if (d.warpOn) out.push(['info', notes.warpCaps + ' They are included below.']);
    const engineApi = data.ports.find((p) => p.id === 'engineApi');
    if (d.engineOn && engineApi && state.ports.engineApi && state.ports.engineApi.enabled) {
      out.push(['warn', engineApi.securityNote]);
    }
    if (state.volumes.config && !state.volumes.config.enabled) {
      out.push(['warn', 'Without the configuration folder your channels and settings are lost whenever the container is replaced.']);
    }
    if (d.engineOn && d.platform.id !== 'amd64' && state.volumes.engineState && !state.volumes.engineState.enabled) {
      out.push(['info', 'Without the engine state folder the ARM engine rebuilds its cache and device id on every container replacement.']);
    }
    if (state.zeronet && state.zeronetEmbedded && !d.platform.zeronetAvailable) {
      out.push(['warn', 'The bundled ZeroNet node is switched off for this platform. ' + data.notes.zeronetArm]);
    }
    if (d.zeronetEmbeddedOn && state.volumes.zeronetData && !state.volumes.zeronetData.enabled) {
      out.push(['info', 'Without the ZeroNet state folder the node re-downloads its sites on every container replacement.']);
    }
    const zeronetUi = data.ports.find((p) => p.id === 'zeronetUi');
    if (d.zeronetEmbeddedOn && zeronetUi && state.ports.zeronetUi && state.ports.zeronetUi.enabled) {
      out.push(['warn', zeronetUi.securityNote + ' Set ZERONET_UI_HOST for access from other machines.']);
    }
    if (state.ipfs && state.ipfsEmbedded && !d.platform.ipfsAvailable) {
      out.push(['warn', 'The embedded IPFS node is switched off for this platform. ' + data.notes.ipfsArmv7]);
    }
    if (d.ipfsEmbeddedOn && state.volumes.ipfsRepo && !state.volumes.ipfsRepo.enabled) {
      out.push(['info', 'Without the IPFS repository folder the node re-initializes with a new identity on every container replacement.']);
    }
    const ipfsGateway = data.ports.find((p) => p.id === 'ipfsGateway');
    if (d.ipfsEmbeddedOn && ipfsGateway && state.ports.ipfsGateway && state.ports.ipfsGateway.enabled) {
      out.push(['info', ipfsGateway.securityNote]);
    }
    if (state.containerName.trim() && !safeName(state.containerName.trim())) {
      out.push(['warn', 'Container names may only contain letters, digits, "_", "." and "-"; using acestream-scraper instead.']);
    }
    const seen = new Map();
    for (const p of portEntries(d)) {
      const key = `${p.host}/${p.proto}`;
      if (seen.has(key) && seen.get(key) !== p.container) {
        out.push(['error', `Host port ${p.host} is used twice — give each service its own host port.`]);
        break;
      }
      seen.set(key, p.container);
    }
    return out;
  }

  // ---------------------------------------------------------------------------
  // Rendering.
  // ---------------------------------------------------------------------------
  function renderFlavors() {
    const box = $('#flavor-options');
    box.replaceChildren();
    for (const f of data.flavors) {
      const input = el('input', { type: 'radio', name: 'flavor', value: f.id, checked: f.id === state.flavor });
      input.addEventListener('change', () => { state.flavor = f.id; update(); });
      const meta = el('div', { class: 'card-meta' }, [
        f.recommended ? el('span', { class: 'chip chip-accent', text: 'Recommended' }) : null,
        f.features.includes('acestream') ? el('span', { class: 'chip', text: 'AceStream engine' }) : null,
        f.features.includes('acexy') ? el('span', { class: 'chip', text: 'Acexy proxy' }) : null,
        el('span', { class: 'chip chip-mono', text: ':' + imageTag(f), 'data-tag-for': f.id })
      ]);
      box.append(el('label', { class: 'card' + (f.id === state.flavor ? ' selected' : '') }, [
        input,
        el('div', { class: 'card-title', text: f.label }),
        el('p', { class: 'card-summary', text: f.summary }),
        meta
      ]));
    }
  }

  function renderPlatforms() {
    const box = $('#platform-options');
    box.replaceChildren();
    for (const p of data.platforms) {
      const input = el('input', { type: 'radio', name: 'platform', value: p.id, checked: p.id === state.platform });
      input.addEventListener('change', () => { state.platform = p.id; update(); });
      const chips = [el('span', { class: 'chip', text: p.engine })];
      if (p.engineSupport === 'experimental') chips.push(el('span', { class: 'chip chip-warm', text: 'Engine: experimental' }));
      if (!p.warpAvailable) chips.push(el('span', { class: 'chip', text: 'No WARP' }));
      box.append(el('label', { class: 'card' + (p.id === state.platform ? ' selected' : '') }, [
        input,
        el('div', { class: 'card-title', text: p.label }),
        el('p', { class: 'card-summary', text: p.summary }),
        el('div', { class: 'card-meta' }, chips)
      ]));
    }
  }

  function renderChannels() {
    const box = $('#channel-options');
    box.replaceChildren();
    for (const c of CHANNELS) {
      const input = el('input', { type: 'radio', name: 'channel', value: c.id, checked: c.id === state.channel });
      input.addEventListener('change', () => { state.channel = c.id; update(); });
      box.append(el('label', { class: 'pill' + (c.id === state.channel ? ' selected' : '') }, [
        input, el('span', { text: c.label }), c.hint ? el('span', { class: 'optional', text: `(${c.hint})` }) : null
      ]));
    }
  }

  function toggleRow(id, title, desc, checked, onChange, disabled) {
    const input = el('input', { type: 'checkbox', id: `toggle-${id}`, checked, disabled: !!disabled });
    input.addEventListener('change', () => { onChange(input.checked); update(); });
    return el('label', { class: 'toggle' + (disabled ? ' disabled' : ''), for: `toggle-${id}` }, [
      input,
      el('span', { class: 'switch', 'aria-hidden': 'true' }),
      el('span', {}, [el('span', { class: 'toggle-title', text: title }), el('p', { class: 'toggle-desc', text: desc })])
    ]);
  }

  function renderFeatures(d) {
    const box = $('#feature-toggles');
    box.replaceChildren();
    const list = el('div', { class: 'toggle-list' });
    if (d.imageHasEngine) {
      list.append(toggleRow('engine', 'Run the AceStream engine in this container',
        `Starts the bundled engine (${d.platform.engine}). Turn off if you already run an engine elsewhere.`,
        state.engine, (v) => { state.engine = v; }));
    }
    if (d.imageHasAcexy) {
      list.append(toggleRow('acexy', 'Run the Acexy proxy',
        'Serves streams to your players over plain HTTP and handles engine sessions for you.',
        state.acexy, (v) => { state.acexy = v; }));
    }
    list.append(toggleRow('warp', 'Route through Cloudflare WARP',
      d.platform.warpAvailable
        ? 'Connects the container through WARP. Adds the required capabilities and TUN device.'
        : data.notes.warpArm,
      d.platform.warpAvailable && state.warp, (v) => { state.warp = v; }, !d.platform.warpAvailable));
    list.append(toggleRow('zeronet', 'Scrape ZeroNet sources',
      data.zeronet.description,
      state.zeronet, (v) => { state.zeronet = v; }));
    if (state.zeronet) {
      list.append(toggleRow('zeronet-embedded', 'Run the bundled ZeroNet node in this container',
        d.platform.zeronetAvailable ? data.zeronet.embeddedDescription : data.notes.zeronetArm,
        d.platform.zeronetAvailable && state.zeronetEmbedded, (v) => { state.zeronetEmbedded = v; }, !d.platform.zeronetAvailable));
    }
    list.append(toggleRow('ipfs', 'Scrape IPFS sources',
      data.ipfs.description,
      state.ipfs, (v) => { state.ipfs = v; }));
    if (state.ipfs) {
      list.append(toggleRow('ipfs-embedded', 'Run the embedded IPFS node in this container',
        d.platform.ipfsAvailable ? data.ipfs.embeddedDescription : data.notes.ipfsArmv7,
        d.platform.ipfsAvailable && state.ipfsEmbedded, (v) => { state.ipfsEmbedded = v; }, !d.platform.ipfsAvailable));
    }
    box.append(list);

    const ext = $('#external-engine-fields');
    ext.hidden = !d.needsExternalEngine;
    $('#external-engine-hint').textContent = data.notes.acexyExternalEngine;

    const zn = $('#zeronet-fields');
    zn.hidden = !d.zeronetExternalOn;
    $('#zeronet-hint').textContent = 'Address of the external ZeroNet service. Use host.docker.internal to reach a service on the Docker host.';
    if (!$('#zeronet-url').value) $('#zeronet-url').value = state.zeronetUrl || data.zeronet.defaultUrl;

    const ipfs = $('#ipfs-fields');
    ipfs.hidden = !d.ipfsExternalOn;
    $('#ipfs-hint').textContent = 'Address of the external IPFS gateway. Use host.docker.internal to reach a node on the Docker host (Kubo’s default gateway port is 8080).';
    if (!$('#ipfs-gateway-url').value) $('#ipfs-gateway-url').value = state.ipfsGatewayUrl || data.ipfs.defaultGatewayUrl;
  }

  function mapRow(kind, item, s, editor) {
    const required = kind === 'port' && item.id === 'web';
    const cb = el('input', { type: 'checkbox', id: `${kind}-${item.id}`, checked: s.enabled, disabled: required,
      'aria-label': `${required ? 'Required: ' : ''}${item.label}` });
    cb.addEventListener('change', () => { s.enabled = cb.checked; update(); });
    const title = el('div', { class: 'map-title' }, [
      el('label', { for: `${kind}-${item.id}`, text: item.label }),
      required ? el('span', { class: 'chip chip-accent', text: 'Required' }) : null,
      kind === 'port' && item.protocols.includes('udp') ? el('span', { class: 'chip', text: 'TCP + UDP' }) : null
    ]);
    return el('div', { class: 'map-row' + (s.enabled ? '' : ' off') }, [
      cb,
      el('div', {}, [title, el('p', { class: 'map-desc', text: item.description }), editor])
    ]);
  }

  function renderPorts(d) {
    const box = $('#port-rows');
    box.replaceChildren();
    const list = el('div', { class: 'row-list' });
    for (const p of d.activePorts) {
      const s = state.ports[p.id];
      const input = el('input', { type: 'number', class: 'mono', min: 1, max: 65535, value: s.host,
        'aria-label': `Host port for ${p.label}`, disabled: !s.enabled });
      input.addEventListener('input', () => { s.host = input.value; updateOutput(); });
      const editor = el('div', { class: 'map-edit' }, [
        el('span', { text: 'Host port' }), input,
        el('span', { class: 'arrow', 'aria-hidden': 'true', text: '→' }),
        el('span', { class: 'target', text: `container ${p.container}/${p.protocols.join('+')}` })
      ]);
      list.append(mapRow('port', p, s, editor));
    }
    box.append(list);
  }

  function renderVolumes(d) {
    const box = $('#volume-rows');
    box.replaceChildren();
    const list = el('div', { class: 'row-list' });
    for (const v of d.activeVolumes) {
      const s = state.volumes[v.id];
      const input = el('input', { type: 'text', class: 'mono wide', value: s.source, spellcheck: 'false',
        'aria-label': `Host folder or volume name for ${v.label}`, disabled: !s.enabled });
      input.addEventListener('input', () => { s.source = input.value; updateOutput(); });
      const editor = el('div', { class: 'map-edit' }, [
        el('span', { text: 'Host folder or volume' }), input,
        el('span', { class: 'arrow', 'aria-hidden': 'true', text: '→' }),
        el('span', { class: 'target', text: v.target })
      ]);
      list.append(mapRow('volume', v, s, editor));
    }
    box.append(list);
  }

  function renderWarnings(d) {
    const box = $('#warnings');
    box.replaceChildren();
    const icons = { info: 'i', warn: '!', error: '×' };
    for (const [level, text] of collectWarnings(d)) {
      box.append(el('p', { class: `warning-card warn-${level}`, role: level === 'error' ? 'alert' : null }, [
        el('span', { class: 'icon', 'aria-hidden': 'true', text: icons[level] }),
        el('span', { text: text })
      ]));
    }
  }

  function renderNextSteps(d) {
    const box = $('#next-steps');
    box.replaceChildren();
    const web = state.ports.web ? (validPort(state.ports.web.host) || 8000) : 8000;
    box.append(el('p', { html: data.notes.afterRun.replace('{webPort}', String(web)).replace(/^Then /, '<strong>Then</strong> ') }));
    box.append(el('p', { text: data.notes.publicBaseUrl }));
    if (d.acexyOn && state.ports.acexy && state.ports.acexy.enabled) {
      const acexyPort = validPort(state.ports.acexy.host) || 8080;
      box.append(el('p', { html: `<strong>Players:</strong> point them at <code>http://&lt;server-ip&gt;:${acexyPort}/ace/getstream?id=&lt;channel id&gt;</code> — the playlist in the web interface uses this base URL once you set it under Settings.` }));
    }
    box.append(el('p', { html: `Full details: <a href="${data.wikiUrl}/Docker">Docker guide</a> · <a href="${data.wikiUrl}/Configuration">Configuration reference</a>.` }));
  }

  function updateOutput() {
    const d = derive();
    $('#run-output').textContent = buildRunCommand(d);
    $('#compose-output').textContent = buildCompose(d);
    renderWarnings(d);
    renderNextSteps(d);
    for (const f of data.flavors) {
      const chip = document.querySelector(`[data-tag-for="${f.id}"]`);
      if (chip) chip.textContent = ':' + imageTag(f);
    }
  }

  function update() {
    const d = derive();
    document.querySelectorAll('#flavor-options .card').forEach((c) => c.classList.toggle('selected', c.querySelector('input').checked));
    document.querySelectorAll('#platform-options .card').forEach((c) => c.classList.toggle('selected', c.querySelector('input').checked));
    document.querySelectorAll('#channel-options .pill').forEach((c) => c.classList.toggle('selected', c.querySelector('input').checked));
    $('#version-field').hidden = state.channel !== 'version';
    renderFeatures(d);
    renderPorts(d);
    renderVolumes(d);
    updateOutput();
  }

  // ---------------------------------------------------------------------------
  // Static wiring (inputs that exist in the HTML).
  // ---------------------------------------------------------------------------
  function bindStatic() {
    const bind = (sel, key, transform) => {
      const node = $(sel);
      node.addEventListener('input', () => { state[key] = transform ? transform(node.value) : node.value; updateOutput(); });
    };
    bind('#version-input', 'version');
    bind('#ext-engine-host', 'extEngineHost');
    bind('#ext-engine-port', 'extEnginePort');
    bind('#zeronet-url', 'zeronetUrl');
    bind('#ipfs-gateway-url', 'ipfsGatewayUrl');
    bind('#container-name', 'containerName');
    bind('#tz-input', 'tz');
    bind('#public-base-url-input', 'publicBaseUrl');
    bind('#tuner-networks-input', 'tunerNetworks');
    bind('#player-max-sessions-input', 'playerMaxSessions');
    $('#restart-policy').addEventListener('change', (e) => { state.restart = e.target.value; updateOutput(); });

    const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
    const select = (tab) => {
      for (const t of tabs) {
        const active = t === tab;
        t.setAttribute('aria-selected', String(active));
        t.tabIndex = active ? 0 : -1;
        $('#' + t.getAttribute('aria-controls')).hidden = !active;
      }
      tab.focus();
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          e.preventDefault();
          const next = (i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length;
          select(tabs[next]);
        }
      });
    });

    document.querySelectorAll('.copy-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const text = $('#' + btn.dataset.copy).textContent;
        try {
          await navigator.clipboard.writeText(text);
        } catch (_) {
          const ta = el('textarea', { text });
          document.body.append(ta);
          ta.select();
          document.execCommand('copy');
          ta.remove();
        }
        const original = btn.textContent;
        btn.textContent = 'Copied';
        btn.classList.add('done');
        setTimeout(() => { btn.textContent = original; btn.classList.remove('done'); }, 1500);
      });
    });
  }

  function init(json) {
    data = json;
    state.flavor = (data.flavors.find((f) => f.recommended) || data.flavors[0]).id;
    state.zeronetUrl = data.zeronet.defaultUrl;
    state.ipfsGatewayUrl = data.ipfs.defaultGatewayUrl;
    $('#tuner-networks-input').placeholder = data.player.tunerNetworksDefault;
    $('#player-max-sessions-input').placeholder = String(data.player.maxSessionsDefault);
    // The engine API, the IPFS gateway and the (unauthenticated) ZeroNet UI
    // work in-container without being published; keep them opt-in.
    for (const p of data.ports) state.ports[p.id] = { enabled: !['engineApi', 'ipfsGateway', 'zeronetUi'].includes(p.id), host: p.defaultHost };
    for (const v of data.volumes) state.volumes[v.id] = { enabled: true, source: v.defaultSource };
    renderFlavors();
    renderPlatforms();
    renderChannels();
    bindStatic();
    update();
    $('#app').hidden = false;
  }

  fetch('builder/runtime-options.json', { cache: 'no-cache' })
    .then((r) => { if (!r.ok) throw new Error(r.statusText); return r.json(); })
    .then(init)
    .catch((err) => {
      console.error('Failed to load runtime-options.json', err);
      $('#load-error').hidden = false;
    });
})();
