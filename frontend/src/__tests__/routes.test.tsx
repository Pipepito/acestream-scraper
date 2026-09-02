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
jest.mock('../pages/Overview', () => ({ __esModule: true, default: () => <h1>Overview</h1> }));
jest.mock('../pages/TVChannels', () => ({ __esModule: true, default: () => <h1>TV Channels</h1> }));
jest.mock('../pages/Search', () => ({ __esModule: true, default: () => <h1>Search</h1> }));
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

  it('exposes eight destinations whose labels are the page titles', () => {
    expect(navItems.map((item) => item.text)).toEqual(['Overview', 'Scraper', 'Search', 'Acestream Channels', 'TV Channels', 'EPG', 'Playlist', 'Settings']);
    expect(getNavTitle('/epg/channels/12')).toBe('EPG');
    expect(getNavTitle('/warp')).toBe('WARP');
  });

  it.each([
    ['/health', 'Overview'],
    ['/stats', 'Overview'],
    ['/dashboard', 'Overview'],
    ['/channels', 'TV Channels'],
    ['/channels/abc', 'TV Channels'],
    ['/search-new', 'Search'],
  ])('redirects %s to the page that holds that information', (from, heading) => {
    expect(LEGACY_REDIRECTS.some((r) => r.from === from.replace(/\/abc$/, '/:id'))).toBe(true);
    renderAt(from);
    expect(screen.getByRole('heading', { level: 1, name: heading })).toBeInTheDocument();
  });
});
