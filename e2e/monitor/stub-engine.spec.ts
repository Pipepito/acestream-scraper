import { stat } from 'node:fs/promises';
import path from 'node:path';
import { test, expect } from '@playwright/test';
import { startStubEngine } from '../src/stub-engine';

test('the two-second media fixture is paced in real time', async () => {
  const fixture = path.resolve(__dirname, '../../backend/tests/docker/fixtures/sample-h264-ac3.m2ts');
  const size = (await stat(fixture)).size;
  const engine = await startStubEngine(fixture);
  const abort = new AbortController();
  try {
    const start = performance.now();
    const response = await fetch(`${engine.url}/content/x/1`, { signal: abort.signal });
    expect(response.ok).toBe(true);
    const reader = response.body!.getReader();
    let bytes = 0;
    while (bytes < size) {
      const chunk = await reader.read();
      expect(chunk.done).toBe(false);
      bytes += chunk.value!.length;
    }
    expect(performance.now() - start).toBeGreaterThanOrEqual(1800);
    await reader.cancel();
  } finally {
    abort.abort();
    await engine.close();
  }
});
