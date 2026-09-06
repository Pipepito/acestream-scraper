import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import LiveTV from '../pages/LiveTV';
import { createAppTheme } from '../theme';

const mockCatalog = jest.fn();
const mockUnassigned = jest.fn();
jest.mock('../hooks/useTVChannels', () => ({ useTVChannelCatalog: () => mockCatalog(), useTVChannel: () => ({}) }));
jest.mock('../hooks/useChannels', () => ({ useAcestreamChannels: (...args: unknown[]) => mockUnassigned(...args) }));
jest.mock('../components/player/ChannelGuide', () => ({ __esModule: true, default: () => <div>Guide</div> }));
jest.mock('../components/player/ChannelPlayerDialog', () => ({ __esModule: true, default: ({ open, title }: { open: boolean; title: string }) => open ? <div role="dialog" aria-label={title} /> : null }));
const renderPage = () => render(<MemoryRouter><ThemeProvider theme={createAppTheme('light')}><LiveTV /></ThemeProvider></MemoryRouter>);

beforeEach(() => {
  jest.clearAllMocks();
  mockCatalog.mockReturnValue({ data: [
    { id: 1, name: 'Watchable', is_active: true, acestream_channels: [{ id: 'one' }] },
    { id: 2, name: 'Empty channel', is_active: true, acestream_channels: [] },
    { id: 3, name: 'Inactive channel', is_active: false, acestream_channels: [{ id: 'two' }] },
  ] });
  mockUnassigned.mockReturnValue({ data: { items: [{ id: 'raw', name: 'Independent', is_online: true }], total: 25 } });
});

it('shows only active TV channels with streams and plays unassigned streams', () => {
  renderPage();
  expect(screen.getByRole('button', { name: 'Watch Watchable' })).toBeEnabled();
  expect(screen.queryByText('Empty channel')).not.toBeInTheDocument();
  expect(screen.queryByText('Inactive channel')).not.toBeInTheDocument();
  expect(mockUnassigned).toHaveBeenCalledWith(expect.objectContaining({ assigned: false, is_online: true, page: 1, page_size: 12 }), expect.anything());
  fireEvent.click(screen.getByRole('button', { name: 'Watch Independent' }));
  expect(screen.getByRole('dialog', { name: 'Independent' })).toBeInTheDocument();
});

it('paginates on the server and resets pagination when searching unassigned streams', () => {
  renderPage();
  fireEvent.click(screen.getByRole('button', { name: 'Go to page 2' }));
  expect(mockUnassigned).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 }), expect.anything());
  fireEvent.change(screen.getByRole('searchbox', { name: 'Find an unassigned stream' }), { target: { value: 'sport' } });
  expect(mockUnassigned).toHaveBeenLastCalledWith(expect.objectContaining({ page: 1, search: 'sport' }), expect.anything());
});

it('keeps the TV catalog available when unassigned streams fail and offers retry', () => {
  const refetch = jest.fn();
  mockUnassigned.mockReturnValue({ isError: true, refetch });
  renderPage();
  expect(screen.getByRole('button', { name: 'Watch Watchable' })).toBeEnabled();
  expect(screen.getByText('Unable to load unassigned streams.')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
  expect(refetch).toHaveBeenCalled();
});

it('shows loading and empty states independently', () => {
  mockUnassigned.mockReturnValue({ isLoading: true });
  const { unmount } = renderPage();
  expect(screen.getByRole('progressbar', { name: 'Loading unassigned streams' })).toBeInTheDocument();
  unmount();
  mockCatalog.mockReturnValue({ data: [] });
  mockUnassigned.mockReturnValue({ data: { items: [], total: 0 } });
  renderPage();
  expect(screen.getByText(/No active TV channels with streams yet/)).toBeInTheDocument();
  expect(screen.getByText('No online streams without a channel.')).toBeInTheDocument();
});
