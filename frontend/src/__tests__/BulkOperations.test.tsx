import React, { act } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { useMediaQuery } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import BulkOperations from '../components/BulkOperations';

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

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
    mockUseMediaQuery.mockReset();
    mockUseMediaQuery.mockReturnValue(false);
  });

  afterEach(() => {
    jest.useRealTimers();
    consoleErrorSpy.mockRestore();
  });

  const click = async (element: Element) => {
    fireEvent.click(element);
    // Flush the component's queued per-channel promise chain inside act so
    // the resulting state updates land before the next assertion.
    await act(async () => {
      await Promise.resolve();
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

  it('uses responsive media queries instead of raw window width for fullscreen mode', () => {
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      writable: true,
      value: 480,
    });

    render(
      <ThemeProvider theme={testTheme}>
        <BulkOperations
          open={true}
          onClose={() => {}}
          selectedChannels={[{ id: '1' }]}
          onBulkEdit={jest.fn()}
          onBulkDelete={jest.fn()}
          onBulkActivate={jest.fn()}
        />
      </ThemeProvider>
    );

    expect(screen.getByRole('dialog')).not.toHaveClass('MuiDialog-paperFullScreen');
  });

  it('keeps success feedback visible until the user dismisses the dialog', async () => {
    const onClose = jest.fn();
    const onBulkDelete = jest.fn().mockResolvedValue(undefined);

    render(
      <ThemeProvider theme={testTheme}>
        <BulkOperations
          open={true}
          onClose={onClose}
          selectedChannels={[{ id: '1', name: 'One' }, { id: '2', name: 'Two' }]}
          onBulkEdit={jest.fn()}
          onBulkDelete={onBulkDelete}
          onBulkActivate={jest.fn()}
        />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: 'Bulk Delete' }));
    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    expect(await screen.findByText('All selected channels deleted successfully.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Delete' })).toBeDisabled();

    jest.useFakeTimers();

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(screen.getByText('All selected channels deleted successfully.')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });
});
