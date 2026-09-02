import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThemeProvider } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import NavBar from '../components/NavBar';
import AppShell from '../components/layout/AppShell';
import { createAppTheme } from '../theme';
import { getShellContentMaxWidth, getShellLayout } from '../styles/layout';
import { mockResponsiveShellQueries } from '../testUtils/mockResponsiveShell';
import { TestMemoryRouter } from '../testUtils/router';
import { useAppThemeMode } from '../bootstrap/AppBootstrap';

jest.mock('../bootstrap/AppBootstrap', () => {
  const actual = jest.requireActual('../bootstrap/AppBootstrap');

  return {
    ...actual,
    useAppThemeMode: jest.fn(),
  };
});

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

const renderWithResponsiveMode = ({
  pathname = '/',
  isPhone = false,
  isDesktop = true,
  isWideDesktop = false,
  ui,
}: {
  pathname?: string;
  isPhone?: boolean;
  isDesktop?: boolean;
  isWideDesktop?: boolean;
  ui: React.ReactElement;
}) => {
  const theme = createAppTheme('light');

  mockResponsiveShellQueries(mockUseMediaQuery, theme, {
    isPhone,
    isDesktop,
    isWideDesktop,
  });

  return render(
    <ThemeProvider theme={theme}>
      <TestMemoryRouter initialEntries={[pathname]}>{ui}</TestMemoryRouter>
    </ThemeProvider>
  );
};

const tab = async () => {
  await userEvent.tab();
};

describe('NavBar responsive shell behavior', () => {
  beforeEach(() => {
    mockUseMediaQuery.mockReset();
    (useAppThemeMode as jest.Mock).mockReturnValue({
      mode: 'light',
      setMode: jest.fn(),
      toggleMode: jest.fn(),
    });
  });

  it('keeps the menu button obvious on phone without repeating the current page title', () => {
    renderWithResponsiveMode({
      pathname: '/scraper',
      isPhone: true,
      isDesktop: false,
      ui: (
        <AppShell>
          <div>Phone content</div>
        </AppShell>
      ),
    });

    expect(screen.getByRole('button', { name: 'open drawer' })).toBeVisible();
    expect(screen.getByRole('banner')).not.toHaveTextContent('Scraper');
    expect(screen.getByRole('button', { name: /switch to dark theme/i })).toBeVisible();
    expect(screen.getByRole('main')).toHaveStyle({
      width: '100%',
      backgroundImage: createAppTheme('light').appTokens.shell.contentGlow,
    });
  });

  it('keeps the drawer persistent on desktop and uses the standard shared shell width before wide desktop', () => {
    const theme = createAppTheme('light');
    const layout = getShellLayout(theme);

    renderWithResponsiveMode({
      pathname: '/tv-channels',
      isPhone: false,
      isDesktop: true,
      isWideDesktop: false,
      ui: (
        <AppShell>
          <div>Desktop content</div>
        </AppShell>
      ),
    });

    expect(screen.queryByRole('button', { name: 'open drawer' })).not.toBeInTheDocument();
    expect(screen.getByRole('banner')).not.toHaveTextContent('TV Channels');
    expect(screen.getAllByText('Acestream Scraper').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /switch to dark theme/i })).toBeVisible();
    expect(screen.getByRole('main')).toHaveStyle({ width: `calc(100% - ${layout.navWidth}px)` });
    const contentWrapper = screen.getByTestId('app-shell-content');
    expect(within(contentWrapper).getByText('Desktop content')).toBeInTheDocument();
    expect(contentWrapper).toHaveStyle({
      maxWidth: `${getShellContentMaxWidth(theme, 'standard')}px`,
    });
  });

  it('expands the shared content wrapper at the wide desktop threshold', () => {
    const theme = createAppTheme('light');

    renderWithResponsiveMode({
      pathname: '/health',
      isPhone: false,
      isDesktop: true,
      isWideDesktop: true,
      ui: (
        <AppShell>
          <div>Wide desktop content</div>
        </AppShell>
      ),
    });

    const contentWrapper = screen.getByTestId('app-shell-content');
    expect(within(contentWrapper).getByText('Wide desktop content')).toBeInTheDocument();
    expect(contentWrapper).toHaveStyle({
      maxWidth: `${getShellContentMaxWidth(theme, 'wide')}px`,
    });
  });

  it('preserves desktop keyboard reachability in grouped nav DOM order', async () => {
    renderWithResponsiveMode({
      pathname: '/scraper',
      isPhone: false,
      isDesktop: true,
      ui: <NavBar />,
    });

    await tab();
    expect(screen.getByRole('button', { name: /switch to dark theme/i })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'Overview' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'Scraper' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'Search' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'Acestream Channels' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'TV Channels' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'EPG' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'Playlist' })).toHaveFocus();

    await tab();
    expect(screen.getByRole('link', { name: 'Settings' })).toHaveFocus();
  });

  it('keeps EPG selected for the mapping rules route', () => {
    renderWithResponsiveMode({
      pathname: '/epg/mappings',
      isPhone: false,
      isDesktop: true,
      ui: <NavBar />,
    });

    expect(screen.getByRole('link', { name: 'EPG' })).toHaveAttribute('aria-current', 'page');
    expect(screen.queryByRole('link', { name: 'EPG Mappings' })).not.toBeInTheDocument();
  });
});
