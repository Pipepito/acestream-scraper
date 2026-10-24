import { createServer, type ServerResponse } from 'node:http';
import type { AddressInfo } from 'node:net';
import { test as base, expect } from '@playwright/test';
import { ErrorMonitor } from '../src/error-monitor';

const test = base.extend<{ server: { url: string; pending: () => number } }>({
  server: async ({}, use) => {
    const pending = new Set<ServerResponse>();
    const server = createServer((req, res) => {
      if (req.url === '/api/pending') {
        pending.add(res);
        res.on('close', () => pending.delete(res));
      } else if (req.url === '/api/broken') {
        req.socket.destroy();
      } else if (req.url === '/api/unavailable') {
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end('{"detail":"unavailable"}');
      } else {
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<title>Monitor transport fixture</title>');
      }
    });
    await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
    try {
      await use({ url: `http://127.0.0.1:${(server.address() as AddressInfo).port}`, pending: () => pending.size });
    } finally {
      for (const response of pending) response.destroy();
      server.closeAllConnections();
      await new Promise<void>(resolve => server.close(() => resolve()));
    }
  },
});

for (const method of ['GET', 'HEAD', 'POST']) {
  test(`explicit ${method} cancellation is classified without hiding mutations`, async ({ page, server }) => {
    const monitor = new ErrorMonitor(page, { allowedApiErrorPatterns: [], allowedConsolePatterns: [] });
    await monitor.start();
    await page.goto(server.url);
    await page.evaluate(method => {
      const state = window as Window & { abortRequest?: AbortController };
      state.abortRequest = new AbortController();
      void fetch('/api/pending', { method, signal: state.abortRequest.signal }).catch(() => {});
    }, method);
    await expect.poll(server.pending).toBe(1);
    await page.evaluate(() => (window as Window & { abortRequest?: AbortController }).abortRequest?.abort());
    await expect.poll(() => monitor.cancelledReads.length + monitor.apiFailures.length).toBe(1);
    expect(monitor.cancelledReads.length).toBe(method === 'POST' ? 0 : 1);
    expect(monitor.apiFailures.length).toBe(method === 'POST' ? 1 : 0);
  });
}

test('navigation cancellation is retained as evidence without a false API failure', async ({ page, server, browserName }) => {
  const monitor = new ErrorMonitor(page, { allowedApiErrorPatterns: [], allowedConsolePatterns: [] });
  await monitor.start();
  await page.goto(server.url);
  await page.evaluate(() => { void fetch('/api/pending').catch(() => {}); });
  await expect.poll(server.pending).toBe(1);
  await page.goto(`${server.url}/next`);
  // Firefox and WebKit report implicit navigation cancellation. Chromium can
  // abandon this fetch without requestfailed; explicit aborts are tested above.
  if (browserName !== 'chromium') {
    await expect.poll(() => monitor.cancelledReads.length).toBe(1);
  }
  expect(monitor.cancelledReads.every(failure => failure.method === 'GET')).toBe(true);
  expect(monitor.apiFailures).toEqual([]);
});

test('real HTTP and socket failures remain errors', async ({ page, server }) => {
  const monitor = new ErrorMonitor(page, { allowedApiErrorPatterns: [], allowedConsolePatterns: [] });
  await monitor.start();
  await page.goto(server.url);
  await page.evaluate(async () => {
    await fetch('/api/unavailable');
    await fetch('/api/broken').catch(() => {});
  });
  await expect.poll(() => monitor.apiFailures.length).toBe(2);
  expect(monitor.apiFailures.map(failure => failure.status).sort((a, b) => a - b)).toEqual([0, 503]);
  expect(monitor.cancelledReads).toEqual([]);
});
