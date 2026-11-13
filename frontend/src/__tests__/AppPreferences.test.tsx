import React, { useEffect, useState } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { AppPreferencesProvider, readPreferences, useAppPreferences } from '../preferences/AppPreferences';
import InterfaceSelector from '../components/InterfaceSelector';
import { createAppTheme } from '../theme';
import { ThemeProvider } from '@mui/material/styles';
import i18n from '../i18n';

const fetchData = jest.fn(async () => 'retained');
const mountMedia = jest.fn();
function Feature() {
  const [draft, setDraft] = useState('');
  useQuery({ queryKey: ['fixture'], queryFn: fetchData, staleTime: Infinity });
  useEffect(() => { mountMedia(); }, []);
  return <><input aria-label="Draft" value={draft} onChange={event => setDraft(event.target.value)} /><video aria-label="Player"><track kind="captions" /></video></>;
}
function Harness() {
  const preferences = useAppPreferences();
  return <ThemeProvider theme={createAppTheme(preferences.mode, preferences.interface)}><InterfaceSelector /><Feature /></ThemeProvider>;
}
beforeEach(() => { localStorage.clear(); jest.clearAllMocks(); });
afterEach(() => { jest.restoreAllMocks(); void i18n.changeLanguage('en'); });

it('defaults unknown interface to cyan and preserves the recognized legacy theme and language', () => {
  localStorage.setItem('app-interface-v1', 'unknown');
  localStorage.setItem('app-theme-mode', 'dark');
  localStorage.setItem('app-language-v1', 'es');
  expect(readPreferences()).toEqual({ value: { interface: 'cyan', mode: 'dark', language: 'es' }, failure: null });
});

it('contains storage read failures', () => {
  jest.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked'); });
  expect(readPreferences()).toMatchObject({ value: { interface: 'cyan' }, failure: 'read' });
});

it('preserves the draft, media node, query cache and open selector across all presets, theme and language', async () => {
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={cache}><AppPreferencesProvider><Harness /></AppPreferencesProvider></QueryClientProvider>);
  const player = screen.getByLabelText('Player');
  fireEvent.change(screen.getByRole('textbox', { name: 'Draft' }), { target: { value: 'Unsaved exact text' } });
  fireEvent.click(screen.getByRole('button', { name: 'Interface' }));
  for (const name of ['Lime', 'Coral / navy', 'Immersive']) {
    fireEvent.click(screen.getByRole('button', { name: new RegExp(name) }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  }
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Language' }));
  fireEvent.click(screen.getByRole('option', { name: 'Español' }));
  await screen.findByRole('dialog', { name: 'Elige tu interfaz' });
  fireEvent.mouseDown(screen.getByRole('combobox', { name: 'Tema' }));
  fireEvent.click(screen.getByRole('option', { name: 'Oscuro' }));
  fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(screen.getByRole('textbox', { name: 'Draft' })).toHaveValue('Unsaved exact text');
  expect(screen.getByLabelText('Player')).toBe(player);
  expect(mountMedia).toHaveBeenCalledTimes(1);
  expect(fetchData).toHaveBeenCalledTimes(1);
  expect(cache.getQueryData(['fixture'])).toBe('retained');
  expect(document.documentElement).toHaveAttribute('lang', 'es');
  expect(localStorage.getItem('app-theme-mode')).toBe('dark');
});

it('applies a preference despite a write failure and retries remembering it', async () => {
  const write = jest.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('quota'); });
  render(<AppPreferencesProvider><InterfaceSelector /></AppPreferencesProvider>);
  fireEvent.click(screen.getByRole('button', { name: 'Interface' }));
  fireEvent.click(screen.getByRole('button', { name: /Lime/ }));
  expect(screen.getByRole('alert')).toHaveTextContent('could not be remembered');
  expect(screen.getByRole('button', { name: /Lime/ })).toHaveAttribute('aria-pressed', 'true');
  write.mockRestore();
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  expect(localStorage.getItem('app-interface-v1')).toBe('lime');
});
