import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import GuideMatchingFields from '../components/GuideMatchingFields';
import GuideCoverage from '../components/GuideCoverage';
import { guideSetupService } from '../services/guideSetupService';

jest.mock('../services/guideSetupService');
const service = jest.mocked(guideSetupService);
function setup(component: React.ReactNode, mode: 'light' | 'dark' = 'light') {
  return render(<ThemeProvider theme={createAppTheme(mode)}><QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><TestMemoryRouter>{component}</TestMemoryRouter></QueryClientProvider></ThemeProvider>);
}
beforeEach(() => {
  jest.resetAllMocks();
  service.config.mockResolvedValue({ enabled: false });
  service.lastRun.mockResolvedValue({ status: 'never' });
  service.coverage.mockResolvedValue({ streams: 1904, linked_streams: 0, guide_channels: 1194 });
});

it.each(['light', 'dark'] as const)('starts disabled and saves an explicit automation choice in %s mode', async mode => {
  service.saveConfig.mockResolvedValue({ enabled: true });
  setup(<GuideMatchingFields />, mode);
  const toggle = await screen.findByRole('checkbox', { name: 'Automatically match guide channels' });
  expect(toggle).not.toBeChecked();
  expect(service.saveConfig).not.toHaveBeenCalled();
  fireEvent.click(toggle);
  await waitFor(() => expect(toggle).toBeChecked());
  expect(service.saveConfig).toHaveBeenCalledWith({ enabled: true }, expect.anything());
  expect(screen.getByRole('link', { name: 'Review guide matches' })).toHaveAttribute('href', '/epg?tab=matching');
});

it('keeps the previous setting when saving fails', async () => {
  service.saveConfig.mockRejectedValue(new Error('offline'));
  setup(<GuideMatchingFields />);
  const toggle = await screen.findByRole('checkbox', { name: 'Automatically match guide channels' });
  fireEvent.click(toggle);
  await screen.findByText(/Could not save automatic guide matching/);
  expect(toggle).not.toBeChecked();
});

it('shows partial guide coverage and points to reviewed setup', async () => {
  setup(<GuideCoverage />);
  await screen.findByText('0 of 1904 streams in your catalogue have a linked guide.');
  expect(screen.getByRole('link', { name: 'Review guide matches' })).toHaveAttribute('href', '/epg?tab=matching');
  expect(screen.getByRole('link', { name: 'Manage EPG sources' })).toHaveAttribute('href', '/epg?tab=sources');
});

it('does not present an unavailable coverage count as zero', async () => {
  service.coverage.mockRejectedValue(new Error('offline'));
  setup(<GuideCoverage />);
  await screen.findByText('Guide coverage could not be loaded.');
  expect(screen.queryByText(/0 of/)).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled();
});
