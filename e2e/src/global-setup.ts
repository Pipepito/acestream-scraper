import type { FullConfig } from '@playwright/test';
import { loadScenario } from './scenario/load';
import { waitForHttp } from './stack';

/**
 * Fail fast with a clear message when the stack is not up, instead of every
 * spec timing out on its first navigation.
 */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = (config.projects[0]?.use.baseURL as string | undefined) ?? 'http://127.0.0.1:8000';
  const scenario = loadScenario();
  await waitForHttp(`${baseURL}/api/v1/health`, 60_000, 'app under test');
  if (process.env.E2E_REQUIRE_ENGINE !== '0') {
    await waitForHttp(`${scenario.stack.engineUrl}/webui/api/service?method=get_version`, 120_000, 'AceStream engine');
    await waitForHttp(`${scenario.stack.acexyUrl}/ace/status`, 60_000, 'Acexy');
  }
  process.stdout.write(`[e2e] stack ready: app=${baseURL} engine=${scenario.stack.engineUrl} acexy=${scenario.stack.acexyUrl} scenario=${scenario.name}\n`);
}
