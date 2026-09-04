import { createServer, type IncomingMessage, type Server, type ServerResponse } from 'node:http';
import { readFile } from 'node:fs/promises';
import type { AddressInfo } from 'node:net';

/**
 * A deterministic stand-in for the AceStream engine.
 *
 * The live engine depends on real peers: a channel that has nobody sharing it
 * right now cannot be told apart from a broken player. This server answers the
 * three calls `EngineClient` makes and then feeds a real MPEG-TS fixture on a
 * loop at roughly broadcast rate, so a playback test either works or points at
 * our own code.
 */
export interface StubEngine {
  /** Base URL to store as the `ace_engine_url` setting. */
  url: string;
  /** Streams served so far — a test can assert the backend actually pulled one. */
  streamCount: () => number;
  /** True once the backend asked the engine to stop the stream. */
  stopped: () => boolean;
  close: () => Promise<void>;
}

/**
 * Pacing: ~25 KB every 50 ms ≈ 500 KB/s, close enough to an SD channel that ffmpeg
 * and the browser buffer the way they would on a live one. The chunk is a whole
 * number of 188-byte TS packets purely so the size reads as a stream size; the
 * consumer sees one byte stream and never the chunk boundaries. The fixture is
 * replayed verbatim on a loop, so a decoder resyncs at each wrap.
 */
const PACKET_BYTES = 188;
const PACKETS_PER_CHUNK = 133;
const CHUNK_INTERVAL_MS = 50;

const json = (res: ServerResponse, body: unknown): void => {
  const payload = JSON.stringify(body);
  res.writeHead(200, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) });
  res.end(payload);
};

/**
 * Start the stub on an ephemeral loopback port.
 *
 * @param fixturePath absolute path to an MPEG-TS file (backend/tests/docker/fixtures/sample-h264-ac3.m2ts).
 */
export async function startStubEngine(fixturePath: string): Promise<StubEngine> {
  const fixture = await readFile(fixturePath);
  if (fixture.length < PACKET_BYTES) throw new Error(`stub engine fixture is too small: ${fixturePath}`);

  let streams = 0;
  let stopped = false;
  const openResponses = new Set<ServerResponse>();
  const timers = new Set<NodeJS.Timeout>();

  const streamFixture = (res: ServerResponse): void => {
    streams += 1;
    openResponses.add(res);
    res.writeHead(200, { 'Content-Type': 'video/mp2t', 'Cache-Control': 'no-store' });

    let offset = 0;
    const chunkBytes = PACKET_BYTES * PACKETS_PER_CHUNK;
    const timer = setInterval(() => {
      if (res.writableEnded || res.destroyed) return;
      // Backpressure: skip this tick rather than growing the socket buffer forever.
      if (res.writableNeedDrain) return;
      const chunk = Buffer.alloc(chunkBytes);
      for (let written = 0; written < chunkBytes; ) {
        const take = Math.min(chunkBytes - written, fixture.length - offset);
        fixture.copy(chunk, written, offset, offset + take);
        written += take;
        offset = (offset + take) % fixture.length;
      }
      res.write(chunk);
    }, CHUNK_INTERVAL_MS);
    timers.add(timer);

    const finish = (): void => {
      clearInterval(timer);
      timers.delete(timer);
      openResponses.delete(res);
    };
    res.on('close', finish);
    res.on('error', finish);
  };

  const server: Server = createServer((req: IncomingMessage, res: ServerResponse) => {
    const requestUrl = new URL(req.url ?? '/', `http://${req.headers.host ?? '127.0.0.1'}`);
    const base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;

    if (requestUrl.pathname === '/ace/getstream') {
      json(res, {
        response: {
          playback_url: `${base}/content/x/1`,
          stat_url: `${base}/ace/stat/x/s`,
          command_url: `${base}/ace/cmd/x/s`,
          is_live: 1,
        },
        error: null,
      });
      return;
    }
    if (requestUrl.pathname === '/content/x/1') {
      streamFixture(res);
      return;
    }
    if (requestUrl.pathname === '/ace/stat/x/s') {
      json(res, { response: { status: 'dl', peers: 3, speed_down: 500, speed_up: 0 }, error: null });
      return;
    }
    if (requestUrl.pathname === '/ace/cmd/x/s') {
      if (requestUrl.searchParams.get('method') === 'stop') stopped = true;
      json(res, { response: { status: 'ok' }, error: null });
      return;
    }
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end('{"error":"not found"}');
  });

  await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
  const { port } = server.address() as AddressInfo;

  return {
    url: `http://127.0.0.1:${port}`,
    streamCount: () => streams,
    stopped: () => stopped,
    close: async () => {
      for (const timer of timers) clearInterval(timer);
      timers.clear();
      for (const res of openResponses) res.destroy();
      openResponses.clear();
      await new Promise<void>((resolve) => server.close(() => resolve()));
    },
  };
}
