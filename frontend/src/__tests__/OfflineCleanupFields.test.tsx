import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import OfflineCleanupFields from '../components/settings/OfflineCleanupFields';
import { getOfflineCleanup, previewOfflineCleanup, saveOfflineCleanup } from '../services/configService';

jest.mock('../services/configService', () => ({ getOfflineCleanup: jest.fn(), previewOfflineCleanup: jest.fn(), saveOfflineCleanup: jest.fn() }));

test('previews without enabling cleanup and saves the chosen cadence explicitly', async () => {
  const config = { enabled: false, offline_days: 14, interval_days: 7, remove_linked: false, rescrape: true };
  jest.mocked(getOfflineCleanup).mockResolvedValue(config);
  jest.mocked(previewOfflineCleanup).mockResolvedValue({ eligible_streams: 3, sources: 1, limit: 500 });
  jest.mocked(saveOfflineCleanup).mockImplementation(async value => value);
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><OfflineCleanupFields /></QueryClientProvider>);
  const enabled = await screen.findByRole('checkbox', { name: 'Automatically remove long-offline AceStreams' });
  expect(enabled).not.toBeChecked();
  fireEvent.click(screen.getByRole('button', { name: 'Preview cleanup' }));
  expect(await screen.findByText(/3 streams from 1 sources qualify now/)).toBeInTheDocument();
  expect(saveOfflineCleanup).not.toHaveBeenCalled();
  fireEvent.click(enabled);
  fireEvent.change(screen.getByRole('spinbutton', { name: 'Run every (days)' }), { target: { value: '10' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save cleanup settings' }));
  await waitFor(() => expect(saveOfflineCleanup).toHaveBeenCalledWith({ ...config, enabled: true, interval_days: 10 }, expect.anything()));
  expect(await screen.findByText('Offline cleanup settings saved.')).toBeInTheDocument();
});
