import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { ApiError } from '../services/apiErrors';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import WarpExclusionsSection from '../components/WarpExclusionsSection';
import WarpStartupSection from '../components/WarpStartupSection';
import { getWarpExclusions, saveWarpExclusions } from '../services/warpService';
import { setupService, type SetupState } from '../services/setupService';

jest.mock('../services/warpService');
jest.mock('../services/setupService', () => ({ setupQueryKey: ['installation-setup'], setupService: { get: jest.fn(), save: jest.fn() } }));
const state = { hosts: [], active_hosts: [], revision: 'a'.repeat(64), applied: true, error: null };
const setup = { runtime: { ENABLE_WARP: true, WARP_ENABLE_NAT: false, WARP_FORCE_IPV4: true }, unavailable: {}, revision: 'b'.repeat(64), setup_complete: false, restart_required: false } as unknown as SetupState;
const renderSection = (node: React.ReactNode) => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><ThemeProvider theme={createAppTheme('light')}>{node}</ThemeProvider></QueryClientProvider>);

beforeEach(() => {
  jest.clearAllMocks();
  (getWarpExclusions as jest.Mock).mockResolvedValue(state);
  (setupService.get as jest.Mock).mockResolvedValue(setup);
});

it('adds the Atresmedia hosts and saves verified exclusions', async () => {
  const user = userEvent.setup();
  (saveWarpExclusions as jest.Mock).mockImplementation(async request => ({ ...state, hosts: request.hosts, active_hosts: request.hosts }));
  renderSection(<WarpExclusionsSection />);
  await user.click(await screen.findByRole('button', { name: 'Add Atresmedia' }));
  await user.click(screen.getByRole('button', { name: 'Save and apply exclusions' }));
  await waitFor(() => expect(saveWarpExclusions).toHaveBeenCalledWith({ hosts: ['api.atresplayer.com', 'atres-live.atresmedia.com'], expected_revision: state.revision }, expect.anything()));
  expect(await screen.findByText('Exclusions saved and applied.')).toBeInTheDocument();
});

it('keeps a saved but unapplied list visible and lets the user retry', async () => {
  const user = userEvent.setup();
  (saveWarpExclusions as jest.Mock).mockResolvedValue({ ...state, hosts: ['example.com'], applied: false, active_hosts: null, error: 'WARP is unavailable.' });
  renderSection(<WarpExclusionsSection />);
  await user.type(await screen.findByRole('textbox', { name: 'Hosts to exclude' }), 'example.com');
  await user.click(screen.getByRole('button', { name: 'Save and apply exclusions' }));
  expect(await screen.findByText(/Saved exclusions are not applied/)).toHaveTextContent('WARP is unavailable.');
  expect(screen.getByRole('textbox', { name: 'Hosts to exclude' })).toHaveValue('example.com');
  expect(screen.getByRole('button', { name: 'Save and apply exclusions' })).toBeEnabled();
});

it('clears managed exclusions without deleting other active hosts', async () => {
  const user = userEvent.setup();
  (getWarpExclusions as jest.Mock).mockResolvedValue({ ...state, hosts: ['example.com'], active_hosts: ['example.com', 'outside.example.com'] });
  (saveWarpExclusions as jest.Mock).mockResolvedValue(state);
  renderSection(<WarpExclusionsSection />);
  await user.clear(await screen.findByRole('textbox', { name: 'Hosts to exclude' }));
  expect(screen.getByText(/Other active WARP exclusions/)).toHaveTextContent('outside.example.com');
  await user.click(screen.getByRole('button', { name: 'Save and apply exclusions' }));
  await waitFor(() => expect(saveWarpExclusions).toHaveBeenCalledWith({ hosts: [], expected_revision: state.revision }, expect.anything()));
});

it('retains edits when saving fails', async () => {
  const user = userEvent.setup();
  (saveWarpExclusions as jest.Mock).mockRejectedValue(new ApiError({ message: 'Exclusions changed in another session. Reload before saving.', code: 'WARP_EXCLUSIONS_CONFLICT', kind: 'unknown', status: 409, canRetry: false }));
  renderSection(<WarpExclusionsSection />);
  await user.type(await screen.findByRole('textbox', { name: 'Hosts to exclude' }), 'example.com');
  await user.click(screen.getByRole('button', { name: 'Save and apply exclusions' }));
  expect(await screen.findByText('Exclusions changed in another session. Reload before saving.')).toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: 'Hosts to exclude' })).toHaveValue('example.com');
});

it('saves only changed startup settings without completing setup', async () => {
  const user = userEvent.setup();
  (setupService.save as jest.Mock).mockResolvedValue({ ...setup, restart_required: true });
  renderSection(<WarpStartupSection />);
  await user.click(await screen.findByRole('checkbox', { name: 'Connect WARP before engines start' }));
  await user.click(screen.getByRole('button', { name: 'Save startup settings' }));
  await waitFor(() => expect(setupService.save).toHaveBeenCalledWith({ runtime: { WARP_ENABLE_NAT: true }, expected_revision: setup.revision, setup_complete: false }, expect.anything()));
  expect(await screen.findByText('Startup settings saved. Restart the container to apply changes.')).toBeInTheDocument();
});
