import React from 'react';
import { act, render, screen } from '@testing-library/react';
import i18n from '../i18n';
import { en, es } from '../i18n/resources';
import { pseudoMessage } from '../i18n/pseudo';
import { useUiText } from '../i18n/useUiText';
import { formatDateTime, formatNumber } from '../utils/formatters';
import { formatRelativeTime } from '../utils/format';
import RecipeResults from '../recipes/RecipeResults';
import { recipeResources } from '../recipes/messages.generated';

const tokens = (value: string) => Array.from(value.matchAll(/\{\{\s*([^}]+?)\s*\}\}/g)).map(match => match[1]).sort();

afterEach(async () => { await act(async () => { await i18n.changeLanguage('en'); }); });

it('covers every application message and retains interpolation tokens in both languages', () => {
  for (const namespace of ['common', 'ui', 'jobs', 'runtime', 'errors', 'status'] as const) {
    expect(Object.keys(es[namespace]).sort()).toEqual(Object.keys(en[namespace]).sort());
    for (const [key, value] of Object.entries(en[namespace])) {
      const translated = (es[namespace] as Record<string, string>)[key];
      expect(translated.trim()).not.toBe('');
      expect(tokens(translated)).toEqual(tokens(value));
    }
  }
});

it('keeps the standalone recipe subset complete and identical to the application messages', () => {
  for (const language of ['en', 'es'] as const) {
    const source = language === 'en' ? en.ui : es.ui;
    for (const [key, value] of Object.entries(recipeResources[language].ui)) {
      expect(value).toBe(source[key as keyof typeof source]);
    }
  }
  expect(Object.keys(recipeResources.en.ui).length).toBeLessThan(Object.keys(en.ui).length / 4);
});

it('selects zero, one and plural messages without exposing suffixes or interpolation markup', async () => {
  function Counts() {
    const t = useUiText();
    return <>{[0, 1, 2].map(count => <p key={count}>{t('{{count}} online stream', { count })}</p>)}</>;
  }
  render(<Counts />);
  expect(screen.getByText('1 online stream')).toBeVisible();
  expect(screen.getByText('0 online streams')).toBeVisible();
  await act(async () => { await i18n.changeLanguage('es'); });
  expect(screen.getByText('0 streams con señal')).toBeVisible();
  expect(screen.getByText('1 stream con señal')).toBeVisible();
  expect(screen.getByText('2 streams con señal')).toBeVisible();
});

it('changes presentation dates and numbers without changing the selected timezone or source data', async () => {
  await act(async () => { await i18n.changeLanguage('es'); });
  expect(formatNumber(1234567.5)).toBe('1.234.567,5');
  expect(formatDateTime('2026-11-08T12:00:00Z')).toContain('nov');
  expect(formatRelativeTime('2026-11-08T11:00:00Z', new Date('2026-11-08T12:00:00Z'))).toBe('hace 1 h');
  render(<RecipeResults result={{ record_count: 1, invalid_count: 0, duplicate_count: 0, issues: [], channels: [{ name: 'News · Noticias 日本語', channel_id: 'a'.repeat(40), metadata: {} }] }} />);
  expect(screen.getByRole('columnheader', { name: 'Nombre' })).toBeVisible();
  expect(screen.getByText('News · Noticias 日本語')).toBeVisible();
});

it('expands pseudo copy while leaving names and other interpolation values unchanged', () => {
  const expanded = pseudoMessage('Watch {{name}} now');
  expect(expanded.length).toBeGreaterThan('Watch {{name}} now'.length);
  expect(tokens(expanded)).toEqual(['name']);
  expect(i18n.t('pseudo-test', { ns: 'ui', defaultValue: expanded, name: 'News 日本語' })).toContain('News 日本語');
});

it('translates every Settings section name, which fall back to English silently when a key is missing', async () => {
  const { translateKnown } = await import('../i18n/text');
  await act(async () => { await i18n.changeLanguage('es'); });
  expect(['Playback', 'Automation', 'Stream links', 'Access', 'Network'].map(name => translateKnown(name)))
    .toEqual(['Reproducción', 'Automatización', 'Enlaces de emisión', 'Acceso', 'Red']);
});
