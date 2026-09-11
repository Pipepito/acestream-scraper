import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import StatusLine from '../components/StatusLine';
import { createAppTheme } from '../theme';

describe('StatusLine', () => {
  it('renders labelled values in one status strip', () => {
    render(
      <ThemeProvider theme={createAppTheme('light')}>
        <StatusLine
          aria-label="Source status"
          items={[
            { label: 'Sources', value: '2 enabled' },
            { label: 'Last scrape', value: '12 min ago', tone: 'success' },
            { label: 'Errors', value: '1', tone: 'error' },
          ]}
          action={<button type="button">Refresh</button>}
        />
      </ThemeProvider>
    );
    const strip = screen.getByRole('status', { name: 'Source status' });
    expect(within(strip).getByText('2 enabled')).toBeInTheDocument();
    expect(within(strip).getByText('12 min ago')).toHaveAttribute('data-tone', 'success');
    expect(within(strip).getByText('1')).toHaveAttribute('data-tone', 'error');
    expect(within(strip).getByRole('button', { name: 'Refresh' })).toBeInTheDocument();
  });
});
