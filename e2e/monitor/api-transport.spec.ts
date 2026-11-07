import { createServer } from 'node:http';
import type { AddressInfo } from 'node:net';
import { test as base, expect } from '@playwright/test';
import { Api } from '../src/api';

const test = base.extend<{ transport: { api: Api; count: (path: string) => number } }>({
  transport: async ({ request }, use) => {
    const counts = new Map<string, number>();
    const server = createServer((req, res) => {
      const path = new URL(req.url ?? '/', 'http://fixture').pathname;
      const count = (counts.get(path) ?? 0) + 1;
      counts.set(path, count);
      if (path === '/unavailable') {
        res.writeHead(503); res.end('Unavailable');
      } else if (path === '/always-reset' || req.method === 'POST' || count === 1) {
        req.socket.destroy();
      } else {
        res.setHeader('Content-Type', 'application/json');
        res.end('{"items":[],"total":0}');
      }
    });
    await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
    try {
      await use({ api: new Api(request, `http://127.0.0.1:${(server.address() as AddressInfo).port}`),
        count: path => counts.get(path) ?? 0 });
    } finally {
      server.closeAllConnections();
      await new Promise<void>(resolve => server.close(() => resolve()));
    }
  },
});

test('typed EPG reads recover from one reset', async ({ transport }) => {
  expect(await transport.api.listEpgChannels(1, 1)).toEqual({ items: [], total: 0 });
  expect(transport.count('/api/v1/epg/channels')).toBe(2);
});

test('raw reads recover from one reset', async ({ transport }) => {
  expect((await transport.api.raw('get', '/read')).status()).toBe(200);
  expect(transport.count('/read')).toBe(2);
});

test('repeated resets still fail after one retry', async ({ transport }) => {
  await expect(transport.api.raw('get', '/always-reset')).rejects.toThrow();
  expect(transport.count('/always-reset')).toBe(2);
});

test('HTTP failures and writes are never retried', async ({ transport }) => {
  expect((await transport.api.raw('get', '/unavailable')).status()).toBe(503);
  expect(transport.count('/unavailable')).toBe(1);
  await expect(transport.api.raw('post', '/write', { action: 'once' })).rejects.toThrow();
  expect(transport.count('/write')).toBe(1);
});
