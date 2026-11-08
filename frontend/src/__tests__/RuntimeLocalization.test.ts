import fs from 'fs';
import path from 'path';
import i18next from 'i18next';
import { runtimeEnglish } from '../i18n/messages/runtime-en';
import { runtimeSpanish } from '../i18n/messages/runtime-es';
import { runtimeHelp, runtimeLabel } from '../i18n/runtime';
import type { RuntimeOption } from '../services/setupService';

const options: RuntimeOption[] = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../../backend/app/config/runtime-options.json'), 'utf8'));
afterEach(async () => { await i18next.changeLanguage('en'); });
it('keeps runtime option copy in sync with the actual server catalogue and translates every stable key', () => {
  const expected = Object.fromEntries(options.flatMap(option => [[`${option.name}.label`, option.label], [`${option.name}.help`, option.help]]));
  expect(runtimeEnglish).toEqual(expected);
  expect(Object.keys(runtimeSpanish).sort()).toEqual(Object.keys(expected).sort());
  for (const option of options) expect(runtimeSpanish[`${option.name}.label` as keyof typeof runtimeSpanish]).toBeTruthy();
});
it('localizes labels while retaining server-supplied defaults and bounds', async () => {
  await i18next.changeLanguage('es');
  const option = options.find(value => value.name === 'PLAYER_MAX_SESSIONS')!;
  expect(runtimeLabel(option)).toBe(runtimeSpanish['PLAYER_MAX_SESSIONS.label']);
  expect(runtimeHelp({ ...option, default: 7, minimum: 2, maximum: 9 })).toContain('7');
  expect(runtimeHelp({ ...option, default: 7, minimum: 2, maximum: 9 })).toContain('2–9');
});
