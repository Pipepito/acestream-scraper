import { test, expect } from '../src/fixtures';
import { httpOk } from '../src/stack';

test.describe('stack readiness', () => {
  test('app, engine, Acexy and IPFS gateway answer', async ({ api, scenario }, testInfo) => {
    const health = await api.health();
    expect(health.status).toBe('healthy');
    expect(health.acestream.status, `engine seen by the app: ${health.acestream.message}`).toBe('online');

    const engineVersion = await fetch(`${scenario.stack.engineUrl}/webui/api/service?method=get_version`).then((r) => r.json() as Promise<{ result?: { version?: string; platform?: string } }>);
    expect(engineVersion.result?.version).toBeTruthy();
    testInfo.annotations.push({ type: 'engine', description: `${engineVersion.result?.platform} ${engineVersion.result?.version}` });

    const acexy = await fetch(`${scenario.stack.acexyUrl}/ace/status`);
    expect(acexy.status).toBe(200);

    if (scenario.stack.ipfsGateway) {
      const source = scenario.scrape.sources[0];
      expect(await httpOk(source.url, 120_000), `IPNS page reachable through ${scenario.stack.ipfsGateway}`).toBe(true);
    }

    const tasks = await api.backgroundTasks();
    const names = tasks.map((t) => t.task_name);
    for (const expected of ['url_scraping', 'channel_status', 'epg_refresh', 'epg_program_cleanup', 'channel_cleanup', 'activity_log_cleanup']) {
      expect(names, 'scheduler jobs registered').toContain(expected);
    }
  });
});
