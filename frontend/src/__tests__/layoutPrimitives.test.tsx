import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Button from '@mui/material/Button';
import { useMediaQuery } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import NavBar from '../components/NavBar';
import AppShell from '../components/layout/AppShell';
import { createAppTheme, type ThemeMode } from '../theme';
import * as layoutStyles from '../styles/layout';
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

interface ResponsiveShellState {
  isPhone?: boolean;
  isDesktop?: boolean;
  isWideDesktop?: boolean;
}

const renderWithTheme = (ui: React.ReactElement, mode: ThemeMode = 'light', responsiveState: ResponsiveShellState = {}) => {
  const theme = createAppTheme(mode);

  mockResponsiveShellQueries(mockUseMediaQuery, theme, responsiveState);

  return {
    theme,
    ...render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>),
  };
};

describe('layout primitives', () => {
  beforeEach(() => {
    mockUseMediaQuery.mockReset();
    (useAppThemeMode as jest.Mock).mockReturnValue({
      mode: 'light',
      setMode: jest.fn(),
      toggleMode: jest.fn(),
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('renders PageHeader copy and actions with stable hardening hooks in %s mode', (mode) => {
    renderWithTheme(
      <PageHeader
        title="Dashboard"
        subtitle="Track operational status."
        actions={
          <>
            <Button>Refresh</Button>
            <Button variant="outlined">Run health check</Button>
          </>
        }
      />,
      mode
    );

    const title = screen.getByRole('heading', { level: 1, name: 'Dashboard' });
    const header = screen.getByRole('banner');
    const copy = screen.getByTestId('page-header-copy');
    const actions = screen.getByTestId('page-header-actions');
    const buttons = screen.getAllByRole('button');

    expect(title).toHaveProperty('tagName', 'H1');
    expect(header).toBeInTheDocument();
    expect(copy).toHaveStyle({ minWidth: '0' });
    expect(actions).toHaveStyle({ flexWrap: 'wrap' });
    expect(screen.getByText('Track operational status.')).toHaveStyle({ marginTop: '4px' });
    expect(screen.getByText('Track operational status.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Run health check' })).toBeInTheDocument();
    expect(buttons).toHaveLength(2);
  });

  it.each<ThemeMode>(['light', 'dark'])('stacks PageHeader actions on phones and realigns them at desktop widths in %s mode', (mode) => {
    const { rerender, theme } = renderWithTheme(
      <PageHeader
        title="Dashboard"
        subtitle="Track operational status."
        actions={
          <>
            <Button>Refresh</Button>
            <Button variant="outlined">Run health check</Button>
          </>
        }
      />,
      mode,
      { isPhone: true, isDesktop: false, isWideDesktop: false }
    );

    expect(screen.getByRole('banner')).toHaveStyle({
      display: 'grid',
      gridTemplateColumns: '1fr',
    });
    expect(screen.getByTestId('page-header-actions')).toHaveStyle({
      flexDirection: 'column',
      alignItems: 'stretch',
      justifyContent: 'flex-start',
      width: '100%',
    });

    mockResponsiveShellQueries(mockUseMediaQuery, theme, { isPhone: false, isDesktop: true, isWideDesktop: true });

    rerender(
      <ThemeProvider theme={theme}>
        <PageHeader
          title="Dashboard"
          subtitle="Track operational status."
          actions={
            <>
              <Button>Refresh</Button>
              <Button variant="outlined">Run health check</Button>
            </>
          }
        />
      </ThemeProvider>
    );

    expect(screen.getByRole('banner')).toHaveStyle({
      display: 'grid',
      gridTemplateColumns: 'minmax(0, 1fr) auto',
    });
    expect(screen.getByTestId('page-header-actions')).toHaveStyle({
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'flex-end',
      width: 'auto',
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('supports wide-desktop PageHeader action alignment overrides in %s mode', (mode) => {
    const { rerender, theme } = renderWithTheme(
      <PageHeader
        title="Dashboard"
        actions={<Button>Refresh</Button>}
        wideActionsAlignment="start"
      />,
      mode,
      { isPhone: false, isDesktop: true, isWideDesktop: false }
    );

    expect(screen.getByTestId('page-header-actions')).toHaveStyle({
      justifyContent: 'flex-end',
      justifySelf: 'end',
    });

    mockResponsiveShellQueries(mockUseMediaQuery, theme, { isPhone: false, isDesktop: true, isWideDesktop: true });

    rerender(
      <ThemeProvider theme={theme}>
        <PageHeader
          title="Dashboard"
          actions={<Button>Refresh</Button>}
          wideActionsAlignment="start"
        />
      </ThemeProvider>
    );

    expect(screen.getByTestId('page-header-actions')).toHaveStyle({
      justifyContent: 'flex-start',
      justifySelf: 'start',
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('supports grouped PageHeader actions so phone layouts keep the primary path first in %s mode', (mode) => {
    renderWithTheme(
      <PageHeader
        title="Dashboard"
        actions={<Button variant="outlined">Open details</Button>}
        primaryActions={<Button variant="contained">Run now</Button>}
      />,
      mode,
      { isPhone: true, isDesktop: false, isWideDesktop: false }
    );

    const actions = screen.getByTestId('page-header-actions');
    const primaryGroup = screen.getByTestId('page-header-primary-actions');
    const secondaryGroup = screen.getByTestId('page-header-secondary-actions');

    expect(actions).toHaveStyle({
      flexDirection: 'column',
      alignItems: 'stretch',
    });
    expect(actions.firstChild).toBe(primaryGroup);
    expect(primaryGroup).toHaveStyle({ width: '100%' });
    expect(secondaryGroup).toHaveStyle({ width: '100%' });
    expect(within(primaryGroup).getByRole('button', { name: 'Run now' })).toBeInTheDocument();
    expect(within(secondaryGroup).getByRole('button', { name: 'Open details' })).toBeInTheDocument();
  });

  it.each<ThemeMode>(['light', 'dark'])('renders ContentSection as an accessible region with stable heading linkage in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <>
        <ContentSection
          title="Controls"
          description="Tune refresh cadence."
          actions={
            <>
              <Button>Save changes</Button>
              <Button variant="outlined">Reset</Button>
            </>
          }
        >
          <div>Section body</div>
        </ContentSection>
        <ContentSection title="Controls">
          <div>Second section body</div>
        </ContentSection>
      </>,
      mode
    );

    const [title, secondTitle] = screen.getAllByRole('heading', { level: 2, name: 'Controls' });
    const description = screen.getByText('Tune refresh cadence.');
    const [firstRegion, secondRegion] = screen.getAllByRole('region', { name: 'Controls' });
    const [copy] = screen.getAllByTestId('content-section-copy');
    const [actions] = screen.getAllByTestId('content-section-actions');
    const buttons = within(firstRegion).getAllByRole('button');

    expect(title).toHaveProperty('tagName', 'H2');
    expect(firstRegion).toBeInTheDocument();
    expect(secondRegion).toBeInTheDocument();
    expect(copy).toHaveStyle({ minWidth: '0' });
    expect(actions).toHaveStyle({ flexWrap: 'wrap' });
    expect(description).toHaveStyle({ marginTop: '4px' });
    expect(description).toBeInTheDocument();
    expect(screen.getByText('Section body')).toBeInTheDocument();
    expect(screen.getByText('Second section body')).toBeInTheDocument();
    expect(buttons).toHaveLength(2);
    expect(title.id).toBeTruthy();
    expect(secondTitle.id).toBeTruthy();
    expect(title.id).not.toEqual(secondTitle.id);
    expect(firstRegion).toHaveAttribute('aria-labelledby', title.id);
    expect(secondRegion).toHaveAttribute('aria-labelledby', secondTitle.id);
    expect(firstRegion).toHaveStyle({
      backgroundColor: theme.appTokens.surface.raised,
      borderColor: theme.appTokens.surface.border,
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('keeps ContentSection actions readable on phones and split-safe on wide layouts in %s mode', (mode) => {
    const { rerender, theme } = renderWithTheme(
      <ContentSection
        title="Controls"
        description="Tune refresh cadence."
        actions={
          <>
            <Button>Save changes</Button>
            <Button variant="outlined">Reset</Button>
          </>
        }
      >
        <div>Section body</div>
      </ContentSection>,
      mode,
      { isPhone: true, isDesktop: false, isWideDesktop: false }
    );

    expect(screen.getByRole('region', { name: 'Controls' })).toHaveStyle({
      width: '100%',
      height: '100%',
    });
    expect(screen.getByTestId('content-section-actions')).toHaveStyle({
      flexDirection: 'column',
      alignItems: 'stretch',
      justifyContent: 'flex-start',
      width: '100%',
    });

    mockResponsiveShellQueries(mockUseMediaQuery, theme, { isPhone: false, isDesktop: true, isWideDesktop: true });

    rerender(
      <ThemeProvider theme={theme}>
        <ContentSection
          title="Controls"
          description="Tune refresh cadence."
          actions={
            <>
              <Button>Save changes</Button>
              <Button variant="outlined">Reset</Button>
            </>
          }
        >
          <div>Section body</div>
        </ContentSection>
      </ThemeProvider>
    );

    expect(screen.getByTestId('content-section-actions')).toHaveStyle({
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'flex-end',
      width: 'auto',
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('provides a wide-layout composition hook for supporting ContentSection placement in %s mode', (mode) => {
    renderWithTheme(
      <ContentSection title="Controls" wideLayout="supporting">
        <div>Section body</div>
      </ContentSection>,
      mode,
      { isPhone: false, isDesktop: true, isWideDesktop: true }
    );

    expect(screen.getByRole('region', { name: 'Controls' })).toHaveStyle({
      gridArea: 'supporting',
      alignSelf: 'start',
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('renders NavBar selected state, readable label, and semantic app bar styling in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <TestMemoryRouter initialEntries={['/']}>
        <NavBar />
      </TestMemoryRouter>,
      mode
    );

    const selectedItem = screen.getByRole('link', { name: 'Dashboard' });
    const selectedLabel = within(selectedItem).getByText('Dashboard');
    const appBar = screen.getByRole('banner');

    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Dashboard' })).not.toBeInTheDocument();
    expect(appBar).not.toHaveTextContent('Dashboard');
    expect(selectedItem).toHaveAttribute('aria-current', 'page');
    expect(selectedItem).toHaveStyle({ backgroundColor: theme.appTokens.shell.activeNavBg });
    expect(selectedLabel).toHaveStyle({ color: theme.appTokens.shell.activeNavText });
    expect(appBar).toHaveStyle({
      backgroundColor: theme.appTokens.shell.appBarBg,
      color: theme.appTokens.text.primary,
      borderBottom: `1px solid ${theme.appTokens.shell.appBarBorder}`,
      boxShadow: 'none',
    });
    expect(screen.getAllByText('Acestream Scraper').length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /switch to dark theme/i })).toBeInTheDocument();
  });

  it('keeps nav selection segment-aware for boundary routes', () => {
    const { unmount } = render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter initialEntries={['/search-archive']}>
          <NavBar />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByRole('link', { name: 'Acestream Search' })).not.toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('banner')).not.toHaveTextContent('Not Found');

    unmount();

    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <TestMemoryRouter initialEntries={['/epg/channels']}>
          <NavBar />
        </TestMemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByRole('link', { name: 'EPG Sources' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('banner')).not.toHaveTextContent('EPG Sources');
  });

  it.each<ThemeMode>(['light', 'dark'])('renders AppShell main background from semantic surface tokens in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <TestMemoryRouter initialEntries={['/']}>
        <AppShell>
          <div>Shell content</div>
        </AppShell>
      </TestMemoryRouter>,
      mode
    );

    const main = screen.getByRole('main');
    const shell = main.parentElement;
    const content = screen.getByText('Shell content').parentElement;

    expect(shell).toHaveStyle({ minWidth: '0' });
    expect(main).toHaveStyle({
      backgroundColor: theme.appTokens.surface.canvas,
      minWidth: '0',
      overflowX: 'hidden',
      backgroundImage: theme.appTokens.shell.contentGlow,
    });
    expect(content).toHaveStyle({
      width: '100%',
      minWidth: '0',
      backgroundColor: theme.appTokens.surface.raised,
      border: `1px solid ${theme.appTokens.surface.border}`,
    });
    expect(screen.getByText('Shell content')).toBeInTheDocument();
  });

  it.each<ThemeMode>(['light', 'dark'])('uses the shared wide shell content width value in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <TestMemoryRouter initialEntries={['/']}>
        <AppShell>
          <div>Shell content</div>
        </AppShell>
      </TestMemoryRouter>,
      mode
    );

    const content = screen.getByText('Shell content').parentElement;

    expect(content).toHaveStyle({
      maxWidth: `${layoutStyles.getShellContentMaxWidth(theme, 'wide')}px`,
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('exposes standard and wide shell content maxima in %s mode', (mode) => {
    const theme = createAppTheme(mode);
    const shellLayout = layoutStyles.getShellLayout(theme);

    expect(shellLayout.standardContentMaxWidth).toBe(1280);
    expect(shellLayout.wideContentMaxWidth).toBeGreaterThan(shellLayout.standardContentMaxWidth);
    expect(layoutStyles.getShellContentMaxWidth(theme, 'standard')).toBe(shellLayout.standardContentMaxWidth);
    expect(layoutStyles.getShellContentMaxWidth(theme, 'wide')).toBe(shellLayout.wideContentMaxWidth);
    expect(shellLayout).not.toHaveProperty('contentMaxWidth');
  });

  it.each<ThemeMode>(['light', 'dark'])('provides a shared wide split-layout helper for primary and supporting regions in %s mode', (mode) => {
    const theme = createAppTheme(mode);
    const { getWidePageSplitLayout } = layoutStyles;

    expect(getWidePageSplitLayout).toEqual(expect.any(Function));
    expect(getWidePageSplitLayout(theme, false)).toBeUndefined();
    expect(getWidePageSplitLayout(theme, true)).toMatchObject({
      display: 'grid',
      gridTemplateColumns: 'minmax(0, 2fr) minmax(280px, 1fr)',
      gridTemplateAreas: 'primary supporting',
      gap: theme.appTokens.layout.pageGap,
      alignItems: 'start',
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('provides shared wide split region hooks for primary and supporting slots in %s mode', (mode) => {
    const theme = createAppTheme(mode);
    const { getWidePageSplitRegionStyles } = layoutStyles as typeof layoutStyles & {
      getWidePageSplitRegionStyles?: (
        active: boolean,
        region?: 'default' | 'primary' | 'supporting'
      ) => Record<string, unknown> | undefined;
    };

    expect(getWidePageSplitRegionStyles).toEqual(expect.any(Function));
    expect(getWidePageSplitRegionStyles?.(false, 'primary')).toBeUndefined();
    expect(getWidePageSplitRegionStyles?.(true, 'default')).toBeUndefined();
    expect(getWidePageSplitRegionStyles?.(true, 'primary')).toMatchObject({
      gridArea: 'primary',
      alignSelf: 'start',
    });
    expect(getWidePageSplitRegionStyles?.(true, 'supporting')).toMatchObject({
      gridArea: 'supporting',
      alignSelf: 'start',
    });
    expect(theme.appTokens.layout.pageGap).toBeGreaterThan(0);
  });

  it('wraps long translated-looking copy without dropping layout hooks', () => {
    renderWithTheme(
      <>
        <PageHeader
          title="EinSehrLangerSeitentitelMitÜbersetzungsCharakterUndKeinenNatürlichenLeerzeichen1234567890"
          subtitle="ÜbersetzungsfreundlicherUntertitelMitExtraLangerVerkettungFürUmbruchTests1234567890"
          actions={<Button>AktionMitExtraLangemNamenFürDenZeilenumbruch</Button>}
        />
        <ContentSection
          title="AbschnittMitSehrLangemTitelFürSchrumpfungsverhalten"
          description="BeschreibungMitExtraLangerZusammensetzungZurPrüfungVonBreakWordUndFlexShrinkVerhalten"
          actions={<Button>ZusätzlicheSekundärAktionMitLangemLabel</Button>}
        >
          <div>Body</div>
        </ContentSection>
      </>
    );

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('EinSehrLangerSeitentitelMitÜbersetzungsCharakterUndKeinenNatürlichenLeerzeichen1234567890');
    expect(screen.getByText('ÜbersetzungsfreundlicherUntertitelMitExtraLangerVerkettungFürUmbruchTests1234567890')).toBeInTheDocument();
    expect(screen.getByTestId('page-header-copy')).toHaveStyle({ minWidth: '0' });
    expect(screen.getByTestId('page-header-actions')).toHaveStyle({ flexWrap: 'wrap' });
    expect(screen.getByRole('button', { name: 'AktionMitExtraLangemNamenFürDenZeilenumbruch' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'AbschnittMitSehrLangemTitelFürSchrumpfungsverhalten' })).toBeInTheDocument();
    expect(screen.getAllByTestId('content-section-copy')[0]).toHaveStyle({ minWidth: '0' });
    expect(screen.getAllByTestId('content-section-actions')[0]).toHaveStyle({ flexWrap: 'wrap' });
    expect(screen.getByRole('button', { name: 'ZusätzlicheSekundärAktionMitLangemLabel' })).toBeInTheDocument();
  });

});
