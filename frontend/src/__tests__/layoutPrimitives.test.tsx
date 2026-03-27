import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import Button from '@mui/material/Button';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import NavBar from '../components/NavBar';
import AppShell from '../components/layout/AppShell';
import { createAppTheme, type ThemeMode } from '../theme';

const renderWithTheme = (ui: React.ReactElement, mode: ThemeMode = 'light') => {
  const theme = createAppTheme(mode);

  return {
    theme,
    ...render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>),
  };
};

describe('layout primitives', () => {
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
    expect(screen.getByText('Track operational status.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Run health check' })).toBeInTheDocument();
    expect(buttons).toHaveLength(2);
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

  it.each<ThemeMode>(['light', 'dark'])('renders NavBar selected state, readable label, and semantic app bar styling in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <MemoryRouter initialEntries={['/']}>
        <NavBar />
      </MemoryRouter>,
      mode
    );

    const selectedItem = screen.getByRole('link', { name: 'Dashboard' });
    const selectedLabel = within(selectedItem).getByText('Dashboard');
    const appBar = screen.getByRole('banner');

    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    expect(selectedItem).toHaveAttribute('aria-current', 'page');
    expect(selectedItem).toHaveStyle({ backgroundColor: theme.appTokens.action.secondaryBg });
    expect(selectedLabel).toHaveStyle({ color: theme.appTokens.action.secondaryText });
    expect(appBar).toHaveStyle({
      backgroundColor: theme.appTokens.surface.panel,
      color: theme.appTokens.text.primary,
      borderBottom: `1px solid ${theme.appTokens.layout.divider}`,
      boxShadow: 'none',
    });
    expect(screen.getAllByText('Acestream Scraper').length).toBeGreaterThan(0);
  });

  it('keeps nav selection segment-aware for boundary routes', () => {
    const { unmount } = render(
      <ThemeProvider theme={createAppTheme('light')}>
        <MemoryRouter initialEntries={['/search-archive']}>
          <NavBar />
        </MemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByRole('link', { name: 'Acestream Search' })).not.toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('banner')).toHaveTextContent('Not Found');

    unmount();

    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <MemoryRouter initialEntries={['/epg/channels']}>
          <NavBar />
        </MemoryRouter>
      </ThemeProvider>
    );

    expect(screen.getByRole('link', { name: 'EPG Sources' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('banner')).toHaveTextContent('EPG Sources');
  });

  it.each<ThemeMode>(['light', 'dark'])('renders AppShell main background from semantic surface tokens in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <MemoryRouter initialEntries={['/']}>
        <AppShell>
          <div>Shell content</div>
        </AppShell>
      </MemoryRouter>,
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
    });
    expect(content).toHaveStyle({
      width: '100%',
      minWidth: '0',
    });
    expect(screen.getByText('Shell content')).toBeInTheDocument();
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
