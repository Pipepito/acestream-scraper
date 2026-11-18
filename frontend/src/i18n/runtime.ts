import i18next from 'i18next';
import type { RuntimeOption } from '../services/setupService';
import { uiText } from './text';
import { getLocale } from './locale';

/** Stable option names select copy; defaults and limits come from the server. */
export function runtimeLabel(option: RuntimeOption): string {
  return i18next.t(`${option.name}.label`, { ns: 'runtime', defaultValue: option.label });
}

export function runtimeHelp(option: RuntimeOption): string {
  const help = i18next.t(`${option.name}.help`, { ns: 'runtime', defaultValue: option.help });
  const value = typeof option.default === 'boolean'
    ? option.default ? uiText('Enabled') : uiText('Disabled')
    : typeof option.default === 'number' ? option.default.toLocaleString(getLocale()) : String(option.default || uiText('Empty'));
  const range = option.minimum != null && option.maximum != null
    ? uiText('Allowed range: {{minimum}}–{{maximum}}.', { minimum: option.minimum, maximum: option.maximum }) : '';
  return [help, uiText('Default: {{value}}.', { value }), range].filter(Boolean).join(' ');
}
