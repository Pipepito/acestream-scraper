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
  it.each<ThemeMode>(['light', 'dark'])('renders PageHeader semantic structure with responsive wrapped actions in %s mode', (mode) => {
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
    const actionGroup = screen.getByTestId('page-header-actions');
    const buttons = within(actionGroup).getAllByRole('button');

    expect(title).toHaveProperty('tagName', 'H1');
    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByText('Track operational status.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Run health check' })).toBeInTheDocument();
    expect(actionGroup).toHaveStyle({
      display: 'flex',
      flexWrap: 'wrap',
    });
    expect(buttons).toHaveLength(2);
  });

  it.each<ThemeMode>(['light', 'dark'])('renders ContentSection semantic surface, structure, and responsive wrapped actions in %s mode', (mode) => {
    const { theme } = renderWithTheme(
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
      mode
    );

    const title = screen.getByRole('heading', { level: 2, name: 'Controls' });
    const description = screen.getByText('Tune refresh cadence.');
    const actionGroup = screen.getByTestId('content-section-actions');
    const buttons = within(actionGroup).getAllByRole('button');

    expect(title).toHaveProperty('tagName', 'H2');
    expect(screen.getByRole('region', { name: 'Controls' })).toBeInTheDocument();
    expect(description).toBeInTheDocument();
    expect(screen.getByText('Section body')).toBeInTheDocument();
    expect(actionGroup).toHaveStyle({
      display: 'flex',
      flexWrap: 'wrap',
    });
    expect(buttons).toHaveLength(2);
    expect(screen.getByRole('region', { name: 'Controls' })).toHaveStyle({
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

    expect(screen.getByRole('main')).toHaveStyle({ backgroundColor: theme.appTokens.surface.canvas });
    expect(screen.getByText('Shell content')).toBeInTheDocument();
  });
});
