import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import App, { LEGACY_REDIRECTS } from '../App';
import { createAppTheme } from '../theme';
import { TestMemoryRouter } from '../testUtils/router';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import { useMediaQuery } from '@mui/material';
import { getNavTitle, navItems } from '../components/layout/navItems';

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');
  return { ...actual, useMediaQuery: jest.fn() };
});
jest.mock('../components/SetupNotice', () => ({ __esModule: true, default: () => null }));
jest.mock('../components/UpdateAvailableNotice', () => ({ __esModule: true, default: () => null }));
jest.mock('../pages/TVDashboard', () => ({ __esModule: true, default: () => <h1>TV dashboard</h1> }));
jest.mock('../pages/SystemDashboard', () => ({ __esModule: true, default: () => <h1>System status</h1> }));
jest.mock('../pages/TVChannels', () => ({ __esModule: true, default: () => <h1>TV Channels</h1> }));
jest.mock('../pages/Search', () => ({ __esModule: true, default: () => <h1>Search</h1> }));
jest.mock('../pages/integrations/PublicAddress', () => ({ __esModule: true, default: () => <h1>Public address</h1> }));
jest.mock('../pages/integrations/WebPlayer', () => ({ __esModule: true, default: () => <h1>Web player</h1> }));
jest.mock('../pages/integrations/RemotePlayers', () => ({ __esModule: true, default: () => <h1>Remote players</h1> }));
jest.mock('../pages/integrations/MediaServers', () => ({ __esModule: true, default: () => <h1>Media servers</h1> }));
jest.mock('../pages/integrations/Telegram', () => ({ __esModule: true, default: () => <h1>Telegram</h1> }));
jest.mock('../bootstrap/AppBootstrap', () => ({ useAppThemeMode: () => ({ mode: 'light', toggleMode: jest.fn(), setMode: jest.fn() }) }));

const renderAt = (path: string) =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <TestMemoryRouter initialEntries={[path]}>
        <App />
      </TestMemoryRouter>
    </ThemeProvider>
  );

describe('routes', () => {
  beforeEach(() => {
    mockResponsiveShellQueries(useMediaQuery as jest.MockedFunction<typeof useMediaQuery>, createAppTheme('light'), { isPhone: false });
  });

  it('exposes destinations whose labels are the page titles', () => {
    expect(navItems.map((item) => item.text)).toEqual(['TV dashboard', 'Live TV', 'Recordings', 'Catalogues', 'Events', 'System status', 'Scraper', 'Search', 'Acestream Channels', 'TV Channels', 'EPG', 'Playlist', 'Public address', 'Web player', 'Remote players', 'Media servers', 'Telegram', 'WARP', 'Settings', 'Changelog']);
    expect(getNavTitle('/')).toBe('TV dashboard');
    expect(getNavTitle('/system')).toBe('System status');
    expect(getNavTitle('/events')).toBe('Events');
    expect(getNavTitle('/changelog')).toBe('Changelog');
    expect(getNavTitle('/epg/channels/12')).toBe('EPG');
    expect(getNavTitle('/integrations/public-address')).toBe('Public address');
    expect(getNavTitle('/integrations/telegram')).toBe('Telegram');
    expect(getNavTitle('/warp')).toBe('WARP');
  });

  it.each([
    ['/integrations', 'Public address'],
    ['/health', 'System status'],
    ['/stats', 'TV dashboard'],
    ['/dashboard', 'TV dashboard'],
    ['/channels', 'TV Channels'],
    ['/channels/abc', 'TV Channels'],
    ['/search-new', 'Search'],
  ])('redirects %s to the page that holds that information', async (from, heading) => {
    expect(LEGACY_REDIRECTS.some((r) => r.from === from.replace(/\/abc$/, '/:id'))).toBe(true);
    renderAt(from);
    expect(await screen.findByRole('heading', { level: 1, name: heading })).toBeInTheDocument();
  });
  it.each([
    ['public-address', 'Public address'], ['web-player', 'Web player'],
    ['remote-players', 'Remote players'], ['media-servers', 'Media servers'], ['telegram', 'Telegram'],
  ])('opens and selects /integrations/%s directly', async (path, title) => {
    renderAt(`/integrations/${path}`);
    expect(await screen.findByRole('heading', { level: 1, name: title })).toBeVisible();
    expect(screen.getByRole('link', { name: title })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('list', { name: 'Integrations' })).toContainElement(screen.getByRole('link', { name: title }));
  });

});
