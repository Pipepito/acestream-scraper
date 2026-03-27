import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import Button from '@mui/material/Button';
import { createAppTheme, type ThemeMode } from '../theme';
import InlineStatusNotice from '../components/state/InlineStatusNotice';
import EmptyState from '../components/state/EmptyState';

const renderWithTheme = (ui: React.ReactElement, mode: ThemeMode = 'light') => {
  const theme = createAppTheme(mode);

  return {
    theme,
    ...render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>),
  };
};

describe('shared state components', () => {
  it.each<ThemeMode>(['light', 'dark'])(
    'renders InlineStatusNotice with semantic status styling, accessible role, and wrapped action layout in %s mode',
    (mode) => {
      const { theme } = renderWithTheme(
        <InlineStatusNotice
          severity="warning"
          title="Long-running refresh needs attention"
          description="Reconnect the guide source if the refresh does not complete after multiple retries."
          action={<Button variant="outlined">Retry sync</Button>}
        />,
        mode
      );

      const notice = screen.getByRole('alert');
      const title = screen.getByText('Long-running refresh needs attention');
      const description = screen.getByText(
        'Reconnect the guide source if the refresh does not complete after multiple retries.'
      );
      const actionGroup = screen.getByTestId('inline-status-notice-action');

      expect(title).toBeInTheDocument();
      expect(title.tagName).not.toBe('H2');
      expect(description).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Retry sync' })).toBeInTheDocument();
      expect(notice).toHaveStyle({
        backgroundColor: theme.appTokens.status.warning.bg,
        borderColor: theme.appTokens.status.warning.border,
        color: theme.appTokens.status.warning.text,
      });
      expect(actionGroup).toHaveStyle({
        display: 'flex',
        flexWrap: 'wrap',
      });
      expect(screen.getByTestId('inline-status-notice-text')).toHaveStyle({ minWidth: '0' });
      expect(description).toHaveStyle({ overflowWrap: 'break-word' });
    }
  );

  it.each([
    { severity: 'error', expectedRole: 'alert' },
    { severity: 'warning', expectedRole: 'alert' },
    { severity: 'info', expectedRole: 'status' },
    { severity: 'success', expectedRole: 'status' },
  ] as const)('maps %s severity to the correct live region role', ({ severity, expectedRole }) => {
    renderWithTheme(<InlineStatusNotice severity={severity} title={`${severity} title`} />);

    expect(screen.getByRole(expectedRole)).toHaveTextContent(`${severity} title`);
  });

  it.each<ThemeMode>(['light', 'dark'])(
    'renders EmptyState as a compact guided surface with optional action in %s mode',
    (mode) => {
      const { theme } = renderWithTheme(
        <EmptyState
          title="No channels connected"
          description="Add a channel source to start monitoring stream health and scheduling guide updates."
          action={<Button variant="contained">Add source</Button>}
        />,
        mode
      );

      const emptyState = screen.getByRole('region', { name: 'No channels connected' });
      const title = screen.getByRole('heading', { level: 2, name: 'No channels connected' });
      const description = screen.getByText(
        'Add a channel source to start monitoring stream health and scheduling guide updates.'
      );

      expect(emptyState).toHaveStyle({
        backgroundColor: theme.appTokens.surface.raised,
        borderColor: theme.appTokens.surface.border,
      });
      expect(title).toBeInTheDocument();
      expect(description).toHaveStyle({ overflowWrap: 'break-word' });
      expect(screen.getByRole('button', { name: 'Add source' })).toBeInTheDocument();
      expect(screen.getByTestId('empty-state-action')).toHaveStyle({
        display: 'flex',
        flexWrap: 'wrap',
      });
    }
  );

  it('always renders the EmptyState description container from the required prop', () => {
    renderWithTheme(<EmptyState title="Nothing to review" description="" />);

    expect(screen.getByText('', { selector: '.MuiTypography-helperText' })).toBeInTheDocument();
  });
});
