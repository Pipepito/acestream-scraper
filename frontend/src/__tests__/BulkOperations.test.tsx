import React, { act } from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import userEvent from '@testing-library/user-event';
import BulkOperations from '../components/BulkOperations';

type LegacyUserEventWithSetup = typeof userEvent & {
  setup?: () => {
    click: (element: Element) => Promise<void>;
  };
};

describe('BulkOperations', () => {
  let consoleErrorSpy: jest.SpyInstance;
  const testTheme = createTheme({
    components: {
      MuiButtonBase: {
        defaultProps: {
          disableRipple: true,
        },
      },
      MuiDialog: {
        defaultProps: {
          transitionDuration: 0,
        },
      },
    },
  });

  beforeEach(() => {
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  const click = async (element: Element) => {
    const legacyUserEvent = userEvent as LegacyUserEventWithSetup;

    if (typeof legacyUserEvent.setup === 'function') {
      const user = legacyUserEvent.setup();
      await act(async () => {
        await user.click(element);
      });
      return;
    }

    await act(async () => {
      userEvent.click(element);
    });
  };

  it('shows error alert on bulk edit failure', async () => {
    const onBulkEdit = jest.fn().mockRejectedValue(new Error('Bulk edit failed'));

    render(
      <ThemeProvider theme={testTheme}>
        <BulkOperations
          open={true}
          onClose={() => {}}
          selectedChannels={[{ id: '1' }]}
          onBulkEdit={onBulkEdit}
          onBulkDelete={jest.fn()}
          onBulkActivate={jest.fn()}
        />
      </ThemeProvider>
    );

    await click(screen.getByRole('button', { name: 'Bulk Edit' }));

    await click(await screen.findByRole('button', { name: 'Update' }));

    expect(await screen.findByText('1 operation(s) failed, 0 succeeded.')).toBeInTheDocument();
    expect(consoleErrorSpy.mock.calls.filter(([message]) => String(message).includes('not wrapped in act'))).toHaveLength(0);
  });
});
