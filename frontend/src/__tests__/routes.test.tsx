import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import App, { LEGACY_REDIRECTS, redirectTarget } from '../App';
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
jest.mock('../pages/WatchHome', () => ({ __esModule: true, default: () => <h1>Watch</h1> }));
jest.mock('../pages/TVDashboard', () => ({ __esModule: true, default: () => <h1>TV dashboard</h1> }));
jest.mock('../pages/SystemDashboard', () => ({ __esModule: true, default: () => <h1>System status</h1> }));
jest.mock('../pages/TVChannels', () => ({ __esModule: true, default: () => <h1>TV Channels</h1> }));
jest.mock('../pages/Search', () => ({ __esModule: true, default: () => <h1>Search</h1> }));
jest.mock('../pages/Scraper', () => ({ __esModule: true, default: () => <h1>Scraper</h1> }));
jest.mock('../pages/integrations/PublicAddress', () => ({ __esModule: true, default: () => <h1>Public address</h1> }));
jest.mock('../pages/integrations/WebPlayer', () => ({ __esModule: true, default: () => <h1>Web player</h1> }));
jest.mock('../pages/integrations/TvCasting', () => ({ __esModule: true, default: () => <h1>TV casting</h1> }));
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
    expect(navItems.map(item => item.text)).toEqual(['Watch', 'Recordings', 'Events', 'Channels', 'Connections', 'Settings', 'System']);
    expect(getNavTitle('/')).toBe('Watch');
    expect(getNavTitle('/system')).toBe('System');
    expect(getNavTitle('/events')).toBe('Events');
    expect(getNavTitle('/epg/channels/12')).toBe('Channels');
    expect(getNavTitle('/integrations/public-address')).toBe('Connections');
    expect(getNavTitle('/scraper/telegram')).toBe('Channels');
    expect(getNavTitle('/warp')).toBe('System');
  });

  it.each([
    ['/integrations', 'Public address'],
    ['/health', 'System status'],
    ['/stats', 'Watch'],
    ['/dashboard', 'Watch'],
    ['/channels', 'TV Channels'],
    ['/channels/abc', 'TV Channels'],
    ['/search-new', 'Search'],
    ['/catalogues', 'Scraper'],
  ])('redirects %s to the page that holds that information', async (from, heading) => {
    expect(LEGACY_REDIRECTS.some((r) => r.from === from.replace(/\/abc$/, '/:id'))).toBe(true);
    renderAt(from);
    expect(await screen.findByRole('heading', { level: 1, name: heading })).toBeInTheDocument();
  });

  it('carries the old query string into the redirect target without overriding its own keys', () => {
    expect(redirectTarget('/scraper?tab=w3u', '?catalogue=1&folder=x')).toBe('/scraper?tab=w3u&catalogue=1&folder=x');
    expect(redirectTarget('/epg?tab=rules', '?tab=other')).toBe('/epg?tab=rules');
    expect(redirectTarget('/', '')).toBe('/');
    expect(redirectTarget('/tv-channels', '?filter=a&filter=b')).toBe('/tv-channels?filter=a&filter=b');
  });
  it.each([
    ['public-address', 'Public address'], ['web-player', 'Web player'],
    ['tv-casting', 'TV casting'], ['remote-players', 'Remote players'], ['media-servers', 'Media servers'], ['telegram', 'Telegram'],
  ])('opens and selects /integrations/%s directly', async (path, title) => {
    renderAt(`/integrations/${path}`);
    expect(await screen.findByRole('heading', { level: 1, name: title })).toBeVisible();
    const destination = path === 'telegram' ? 'Channels' : 'Connections';
    expect(screen.getByRole('link', { name: destination })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('list', { name: 'Main navigation' })).toContainElement(screen.getByRole('link', { name: destination }));
  });

});
