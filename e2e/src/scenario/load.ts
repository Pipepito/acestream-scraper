import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { ScenarioSchema, type Scenario, type ScrapeSource } from './schema';

const SCENARIO_DIR = path.resolve(__dirname, '..', '..', 'scenarios');

export type Target = 'local' | 'docker';

export function currentTarget(): Target {
  return process.env.E2E_TARGET === 'docker' ? 'docker' : 'local';
}

/** Resolve the scenario file: E2E_SCENARIO may be a name (scenarios/<name>.json) or a path. */
export function scenarioPath(): string {
  const requested = process.env.E2E_SCENARIO ?? 'default';
  const asPath = path.isAbsolute(requested) ? requested : path.resolve(process.cwd(), requested);
  if (requested.endsWith('.json') && existsSync(asPath)) return asPath;
  return path.join(SCENARIO_DIR, `${requested}.json`);
}

let cached: Scenario | undefined;

export function loadScenario(): Scenario {
  if (cached) return cached;
  const file = scenarioPath();
  if (!existsSync(file)) {
    throw new Error(`Scenario file not found: ${file} (set E2E_SCENARIO to a name under e2e/scenarios or a path)`);
  }
  const parsed = ScenarioSchema.safeParse(JSON.parse(readFileSync(file, 'utf8')));
  if (!parsed.success) {
    throw new Error(`Scenario ${file} is invalid:\n${parsed.error.issues.map((i) => `  ${i.path.join('.')}: ${i.message}`).join('\n')}`);
  }
  cached = parsed.data;
  return cached;
}

/** The scrape URL the app under test must fetch for this target. */
export function scrapeUrlFor(source: ScrapeSource, target: Target = currentTarget()): string {
  return target === 'docker' && source.dockerUrl ? source.dockerUrl : source.url;
}

export type { Scenario, ScrapeSource, SearchQuery, EpgSource, TvChannelSpec } from './schema';
