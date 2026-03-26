import React from 'react';
import { render, screen } from '@testing-library/react';
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
  it.each<ThemeMode>(['light', 'dark'])('renders PageHeader semantic typography in %s mode', (mode) => {
    renderWithTheme(
      <PageHeader
        title="Dashboard"
        subtitle="Track operational status."
        actions={<Button>Refresh</Button>}
      />,
      mode
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Dashboard' })).toHaveClass('MuiTypography-pageTitle');
    expect(screen.getByText('Track operational status.')).toHaveClass('MuiTypography-helperText');
    expect(screen.getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
  });

  it.each<ThemeMode>(['light', 'dark'])('renders ContentSection semantic surface and typography in %s mode', (mode) => {
    const { theme } = renderWithTheme(
      <ContentSection title="Controls" description="Tune refresh cadence.">
        <div>Section body</div>
      </ContentSection>,
      mode
    );

    const title = screen.getByRole('heading', { level: 2, name: 'Controls' });
    const description = screen.getByText('Tune refresh cadence.');
    const paper = title.closest('.MuiPaper-root');

    expect(title).toHaveClass('MuiTypography-sectionTitle');
    expect(description).toHaveClass('MuiTypography-helperText');
    expect(screen.getByText('Section body')).toBeInTheDocument();
    expect(paper).toHaveStyle({
      backgroundColor: theme.appTokens.surface.raised,
      borderColor: theme.appTokens.surface.border,
    });
  });

  it.each<ThemeMode>(['light', 'dark'])('renders NavBar selected state from semantic tokens in %s mode', (mode) => {
    const { theme, container } = renderWithTheme(
      <MemoryRouter initialEntries={['/']}>
        <NavBar />
      </MemoryRouter>,
      mode
    );

    const selectedItem = container.querySelector('.MuiListItemButton-root.Mui-selected');
    const drawerPaper = container.querySelector('.MuiDrawer-paper');

    expect(screen.getAllByText('Dashboard').length).toBeGreaterThan(0);
    expect(selectedItem).toHaveStyle({ backgroundColor: theme.appTokens.action.secondaryBg });
    expect(drawerPaper).toHaveStyle({ backgroundColor: theme.appTokens.surface.panel });
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
