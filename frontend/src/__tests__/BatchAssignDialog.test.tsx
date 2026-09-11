import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { useMediaQuery } from '@mui/material';
import BatchAssignDialog from '../components/BatchAssignDialog';

jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');

  return {
    ...actual,
    useMediaQuery: jest.fn(),
  };
});

const mockUseMediaQuery = useMediaQuery as jest.MockedFunction<typeof useMediaQuery>;

describe('BatchAssignDialog', () => {
  const testTheme = createTheme({
    components: {
      MuiDialog: {
        defaultProps: {
          transitionDuration: 0,
        },
      },
    },
  });

  const renderDialog = (props: Partial<React.ComponentProps<typeof BatchAssignDialog>> = {}) =>
    render(
      <ThemeProvider theme={testTheme}>
        <BatchAssignDialog
          open={true}
          onClose={jest.fn()}
          selectedChannels={[{ id: '1' }, { id: '2' }]}
          groups={['Sports', 'News']}
          onAssign={jest.fn().mockResolvedValue(undefined)}
          {...props}
        />
      </ThemeProvider>
    );

  beforeEach(() => {
    mockUseMediaQuery.mockReset();
    mockUseMediaQuery.mockReturnValue(false);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('uses responsive media queries instead of raw window width for fullscreen mode', () => {
    Object.defineProperty(window, 'innerWidth', {
      configurable: true,
      writable: true,
      value: 480,
    });

    renderDialog();

    expect(screen.getByRole('dialog')).not.toHaveClass('MuiDialog-paperFullScreen');
  });

  it('keeps success feedback visible until the user dismisses the dialog', async () => {
    jest.useFakeTimers();
    const onClose = jest.fn();

    renderDialog({ onClose });

    fireEvent.mouseDown(screen.getByRole('combobox'));
    fireEvent.click(await screen.findByRole('option', { name: 'Sports' }));
    fireEvent.click(screen.getByRole('button', { name: 'Assign' }));

    expect(await screen.findByText('Assigned successfully!')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Assign' })).toBeDisabled();

    await act(async () => {
      jest.advanceTimersByTime(1500);
    });

    expect(screen.getByText('Assigned successfully!')).toBeInTheDocument();
    expect(onClose).not.toHaveBeenCalled();
  });
});
