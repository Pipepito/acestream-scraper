import React from 'react';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import StoragePanel from '../components/overview/StoragePanel';
import { systemService } from '../services/systemService';
import { createAppTheme } from '../theme';

jest.mock('../services/systemService', () => ({ systemService: { getStorage: jest.fn() } }));
const getStorage = systemService.getStorage as jest.Mock;
const mount = () => render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><ThemeProvider theme={createAppTheme('light')}><StoragePanel /></ThemeProvider></QueryClientProvider>);

it('shows mounted usage, partial size, shared free space and deprecation guidance', async () => {
  getStorage.mockResolvedValue({ checked_at: new Date().toISOString(), mount_detection: 'available', configuration_warnings: [{ legacy: 'SCRAPER_DB_URL', replacement: 'DATABASE_URL', selected: 'SCRAPER_DB_URL' }], directories: [
    { path: '/app/config', mounted: true, read_only: true, directory_bytes: 1048576, size_complete: false, filesystem_free_bytes: 1073741824, filesystem_total_bytes: 2147483648, message: 'Partial size: scan limit or unreadable entries.' },
  ] });
  mount();
  expect(await screen.findByText('/app/config')).toBeInTheDocument();
  expect(screen.getByText('At least 1 MiB')).toBeInTheDocument();
  expect(screen.getByText('1 GiB')).toBeInTheDocument();
  expect(screen.getByText('Read only')).toBeInTheDocument();
  expect(screen.getByText(/old name still works/)).toBeInTheDocument();
  expect(screen.getByText(/Free space is shared/)).toBeInTheDocument();
});

it('keeps unavailable sizes distinct from zero', async () => {
  getStorage.mockResolvedValue({ checked_at: new Date().toISOString(), mount_detection: 'unavailable', directories: [{ path: '/missing', directory_bytes: null }] });
  mount();
  expect(await screen.findByText('/missing')).toBeInTheDocument();
  expect(screen.getByText('Mount unknown')).toBeInTheDocument();
  expect(screen.getAllByText('Unavailable')).toHaveLength(3);
});

it('offers refresh after an error', async () => {
  getStorage.mockRejectedValue(new Error('Unavailable'));
  mount();
  expect(await screen.findByText(/Could not read storage/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Refresh storage' })).toBeEnabled();
});
