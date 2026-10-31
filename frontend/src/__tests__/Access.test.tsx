import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { AccessContext } from '../components/access/AccessContext';
import AccessSettings from '../components/access/AccessSettings';
import AccountSetup from '../components/access/AccountSetup';
import PasswordForm from '../components/access/PasswordForm';
import AccessGate from '../components/access/AccessGate';
import CastControls from '../components/player/CastControls';
import { accessService, type AccessStatus } from '../services/accessService';
import { castService } from '../services/castService';
import { loadBrowserCast } from '../services/browserCast';
import { TestMemoryRouter } from '../testUtils/router';
import { ApiError } from '../services/apiErrors';

jest.mock('../services/accessService', () => ({ ...jest.requireActual('../services/accessService'), accessService: {
  users: jest.fn(), policy: jest.fn(), savePolicy: jest.fn(), credentials: jest.fn(), sessions: jest.fn(),
  status: jest.fn(), bootstrap: jest.fn(), password: jest.fn(), login: jest.fn(), logout: jest.fn(),
} }));
jest.mock('../services/castService', () => ({ castService: { capabilities: jest.fn(), devices: jest.fn(), sessions: jest.fn(), start: jest.fn(), command: jest.fn() } }));
jest.mock('../services/browserCast', () => ({ loadBrowserCast: jest.fn(), startBrowserCast: jest.fn(), stopBrowserCast: jest.fn() }));

const pending: AccessStatus = { mode: 'pending', user: null, permissions: [], csrf: 'csrf', legacy_token: false };
const refresh = jest.fn().mockResolvedValue(undefined);
function wrapper(child: React.ReactNode, status = pending) {
  return render(<ThemeProvider theme={createAppTheme('light')}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}>
    <TestMemoryRouter><AccessContext.Provider value={{ status, refresh }}>{child}</AccessContext.Provider></TestMemoryRouter>
  </QueryClientProvider></ThemeProvider>);
}
beforeEach(() => { jest.clearAllMocks(); (accessService.bootstrap as jest.Mock).mockResolvedValue({}); });

test('first-run setup explains the choice and can continue without accounts', async () => {
  wrapper(<AccountSetup />);
  expect(screen.getByRole('checkbox', { name: 'Enable user management' })).toBeChecked();
  fireEvent.click(screen.getByRole('checkbox', { name: 'Enable user management' }));
  expect(screen.getByText(/Anyone who can reach this installation can manage it/)).toBeVisible();
  fireEvent.click(screen.getByRole('button', { name: 'Continue without accounts' }));
  await waitFor(() => expect(accessService.bootstrap).toHaveBeenCalledWith(expect.objectContaining({ enabled: false })));
  await waitFor(() => expect(refresh).toHaveBeenCalled());
});

test('account setup confirms passwords before submission', async () => {
  wrapper(<AccountSetup />);
  fireEvent.change(screen.getByLabelText(/Administrator username/), { target: { value: 'owner' } });
  fireEvent.change(screen.getByLabelText(/^Password/), { target: { value: 'long enough password' } });
  fireEvent.change(screen.getByLabelText(/Confirm password/), { target: { value: 'different long password' } });
  fireEvent.click(screen.getByRole('button', { name: 'Create administrator and continue' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('The passwords do not match.');
  expect(accessService.bootstrap).not.toHaveBeenCalled();
});

test('account setup preserves actionable account errors', async () => {
  (accessService.bootstrap as jest.Mock).mockRejectedValue(new ApiError({
    status: 409, kind: 'unknown', canRetry: false, message: 'Accounts were already configured. Reload this page.',
  }));
  wrapper(<AccountSetup />);
  fireEvent.click(screen.getByRole('checkbox', { name: 'Enable user management' }));
  fireEvent.click(screen.getByRole('button', { name: 'Continue without accounts' }));
  expect(await screen.findByText('Accounts were already configured. Reload this page.')).toBeVisible();
  expect(refresh).not.toHaveBeenCalled();
});

test('pending setup prevents private views from mounting', async () => {
  (accessService.status as jest.Mock).mockResolvedValue(pending);
  const privateMount = jest.fn();
  function Private() { privateMount(); return <div>Private settings</div>; }
  wrapper(<AccessGate><Private /></AccessGate>);
  await screen.findByRole('checkbox', { name: 'Enable user management' });
  expect(privateMount).not.toHaveBeenCalled();
});

test('password changes require the current password and refresh access after success', async () => {
  (accessService.password as jest.Mock).mockResolvedValue(undefined);
  wrapper(<PasswordForm />);
  fireEvent.change(screen.getByLabelText(/Current password/), { target: { value: 'old long password' } });
  fireEvent.change(screen.getByLabelText(/^New password/), { target: { value: 'new long password' } });
  fireEvent.change(screen.getByLabelText(/Confirm new password/), { target: { value: 'new long password' } });
  fireEvent.click(screen.getByRole('button', { name: 'Change password' }));
  await waitFor(() => expect(accessService.password).toHaveBeenCalledWith({ current_password: 'old long password', password: 'new long password', password_confirmation: 'new long password' }));
  await waitFor(() => expect(refresh).toHaveBeenCalled());
});

test('remote visitors cannot enumerate server TVs and see browser compatibility guidance', async () => {
  (castService.capabilities as jest.Mock).mockResolvedValue({ server_devices: false, compatibility_conversion: false, media_url_configured: false, message: 'Server devices can only be controlled from an approved home network' });
  (loadBrowserCast as jest.Mock).mockResolvedValue(false);
  wrapper(<CastControls contentId={'a'.repeat(40)} audioIndex={null} subtitleIndex={null} />, { ...pending, mode: 'accounts', permissions: ['cast', 'live'] });
  fireEvent.click(screen.getByRole('button', { name: 'Cast…' }));
  expect(await screen.findByText(/This browser cannot discover Cast devices/)).toBeVisible();
  await screen.findByText(/approved home network/);
  expect(castService.devices).not.toHaveBeenCalled();
  expect(castService.sessions).not.toHaveBeenCalled();
});

test('saving access updates cached values and preserves them when revisiting the page', async () => {
  const initial = { public_features: [], public_playlists: false, local_iptv: false, local_networks: [], home_networks: [], remote_casting: false, compatibility_conversion: false, cast_media_url: '' };
  (accessService.policy as jest.Mock).mockResolvedValue(initial);
  (accessService.users as jest.Mock).mockResolvedValue([]);
  (accessService.sessions as jest.Mock).mockResolvedValue([]);
  (accessService.credentials as jest.Mock).mockResolvedValue([]);
  (accessService.savePolicy as jest.Mock).mockResolvedValue({ ...initial, local_iptv: true, local_networks: ['192.168.1.0/24'] });
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } });
  const status: AccessStatus = { ...pending, mode: 'accounts' };
  function Page({ visible }: { visible: boolean }) {
    return <ThemeProvider theme={createAppTheme('light')}><QueryClientProvider client={cache}><AccessContext.Provider value={{ status, refresh }}>{visible ? <AccessSettings /> : null}</AccessContext.Provider></QueryClientProvider></ThemeProvider>;
  }
  const view = render(<Page visible />);
  fireEvent.click(await screen.findByRole('checkbox', { name: 'Allow IPTV without credentials on trusted local networks' }));
  fireEvent.change(screen.getByLabelText('Local IPTV networks'), { target: { value: '192.168.1.12/24' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save access policy' }));
  await screen.findByText('Access policy saved.');
  expect(accessService.savePolicy).toHaveBeenCalledWith({ public_features: [], public_playlists: false, local_iptv: true, local_networks: ['192.168.1.12/24'] });
  expect(screen.queryByText('Server-device casting')).not.toBeInTheDocument();
  view.rerender(<Page visible={false} />);
  view.rerender(<Page visible />);
  expect(await screen.findByRole('checkbox', { name: 'Allow IPTV without credentials on trusted local networks' })).toBeChecked();
  expect(screen.getByLabelText('Local IPTV networks')).toHaveValue('192.168.1.0/24');
  cache.clear();
});

test('casting is offered when user management is disabled', async () => {
  (castService.capabilities as jest.Mock).mockResolvedValue({ server_devices: true, compatibility_conversion: false, media_url_configured: true });
  (castService.devices as jest.Mock).mockResolvedValue([{ id: 'tv', name: 'Living room', model: 'Android TV' }]);
  (castService.sessions as jest.Mock).mockResolvedValue([]);
  (loadBrowserCast as jest.Mock).mockResolvedValue(false);
  wrapper(<CastControls contentId={'a'.repeat(40)} audioIndex={null} subtitleIndex={null} />, { ...pending, mode: 'open' });
  fireEvent.click(screen.getByRole('button', { name: 'Cast…' }));
  await screen.findByRole('combobox', { name: 'TV' });
  await waitFor(() => expect(castService.devices).toHaveBeenCalled());
  expect(screen.getByRole('button', { name: 'Find TVs' })).toBeVisible();
});
