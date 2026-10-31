import React from 'react';
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { AccessContext } from '../components/access/AccessContext';
import TvCasting from '../pages/integrations/TvCasting';
import { castService } from '../services/castService';
import { navItems } from '../components/layout/navItems';

jest.mock('../services/castService', () => ({ castService: {
  settings: jest.fn(), saveSettings: jest.fn(), capabilities: jest.fn(), devices: jest.fn(), discover: jest.fn(), trustHome: jest.fn(),
} }));
const settings = { home_networks: [], remote_casting: false, cast_media_url: '', compatibility_conversion: false };
function renderPage(admin = false) {
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return { cache, ...render(<ThemeProvider theme={createAppTheme('light')}><QueryClientProvider client={cache}><TestMemoryRouter>
    <AccessContext.Provider value={{ status: { mode: admin ? 'accounts' : 'open', user: admin ? { id: 'owner', username: 'owner', administrator: true, enabled: true, permissions: [] } : null, permissions: [], csrf: '', legacy_token: false }, refresh: jest.fn() }}><TvCasting /></AccessContext.Provider>
  </TestMemoryRouter></QueryClientProvider></ThemeProvider>) };
}
beforeEach(() => {
  jest.clearAllMocks();
  (castService.settings as jest.Mock).mockResolvedValue(settings);
  (castService.capabilities as jest.Mock).mockResolvedValue({ server_devices: true, home_connection: true, media_url_configured: true, media_url: 'http://app.test', compatibility_conversion: false });
  (castService.devices as jest.Mock).mockResolvedValue([]);
});

test('has a dedicated menu entry and discovers TVs without account or address setup', async () => {
  expect(navItems).toContainEqual(expect.objectContaining({ text: 'TV casting', path: '/integrations/tv-casting', section: 'Integrations' }));
  (castService.discover as jest.Mock).mockResolvedValue([{ id: 'tv', name: 'Living room', model: 'Android TV' }]);
  const view = renderPage();
  expect(screen.getByRole('heading', { level: 1, name: 'TV casting' })).toBeVisible();
  fireEvent.click(await screen.findByRole('button', { name: 'Find TVs' }));
  expect(await screen.findByText('Living room')).toBeVisible();
  expect(castService.discover).toHaveBeenCalledWith();
  expect(screen.queryByLabelText(/Administrator password/)).not.toBeInTheDocument();
  view.unmount(); view.cache.clear();
});

test('casting saves normalized settings to the shared cache', async () => {
  (castService.saveSettings as jest.Mock).mockResolvedValue({ ...settings, compatibility_conversion: true });
  const view = renderPage();
  fireEvent.click(await screen.findByRole('checkbox', { name: 'Offer H.264 compatibility conversion' }));
  fireEvent.click(screen.getByRole('button', { name: 'Save casting settings' }));
  await screen.findByText('TV casting settings saved.');
  expect(view.cache.getQueryData(['cast-settings'])).toEqual({ ...settings, compatibility_conversion: true });
  view.unmount(); view.cache.clear();
});

test('public-address home trust requires explicit confirmation and does not enable remote casting', async () => {
  (castService.capabilities as jest.Mock).mockResolvedValue({ server_devices: false, home_connection: false, message: 'Connection is unverified' });
  (castService.trustHome as jest.Mock).mockResolvedValue({ ...settings, home_networks: ['8.8.4.4/32'] });
  const view = renderPage(true);
  const trust = await screen.findByRole('button', { name: 'Trust this home connection' });
  expect(trust).toBeDisabled();
  expect(castService.devices).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('checkbox', { name: 'I am connected to my home network now' }));
  fireEvent.click(trust);
  await waitFor(() => expect(castService.trustHome).toHaveBeenCalledTimes(1));
  await waitFor(() => expect(view.cache.getQueryData(['cast-settings'])).toEqual({ ...settings, home_networks: ['8.8.4.4/32'] }));
  expect(castService.saveSettings).not.toHaveBeenCalled();
  view.unmount(); view.cache.clear();
});


test('casting displays refreshed preferences without replacing unsaved edits', async () => {
  const view = renderPage(true);
  await screen.findByRole('button', { name: 'Save casting settings' });
  fireEvent.click(screen.getByRole('button', { name: 'Advanced connection settings' }));
  act(() => { view.cache.setQueryData(['cast-settings'], { ...settings, compatibility_conversion: true, remote_casting: true, home_networks: ['192.168.1.0/24'], cast_media_url: 'http://192.168.1.10:8000' }); });
  await waitFor(() => expect(screen.getByRole('checkbox', { name: 'Offer H.264 compatibility conversion' })).toBeChecked());
  expect(screen.getByRole('checkbox', { name: /Allow accounts with casting permission/ })).toBeChecked();
  expect(screen.getByLabelText('Allowed home networks')).toHaveValue('192.168.1.0/24');
  expect(screen.getByLabelText('Application address for TVs')).toHaveValue('http://192.168.1.10:8000');
  fireEvent.change(screen.getByLabelText('Allowed home networks'), { target: { value: '192.168.2.12/24' } });
  act(() => { view.cache.setQueryData(['cast-settings'], settings); });
  expect(screen.getByLabelText('Allowed home networks')).toHaveValue('192.168.2.12/24');
  (castService.saveSettings as jest.Mock).mockResolvedValue({ ...settings, home_networks: ['192.168.2.0/24'] });
  fireEvent.click(screen.getByRole('button', { name: 'Save casting settings' }));
  await screen.findByText('TV casting settings saved.');
  expect(screen.getByLabelText('Allowed home networks')).toHaveValue('192.168.2.0/24');
  view.unmount(); view.cache.clear();
});
