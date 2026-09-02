import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ScheduleView from '../components/epg/ScheduleView';
import { createAppTheme } from '../theme';

const mockUseEPGPrograms = jest.fn();
jest.mock('../hooks/useEPG', () => ({
  useEPGPrograms: (...args: unknown[]) => mockUseEPGPrograms(...args),
}));

const now = new Date(2026, 2, 25, 12, 0, 0);
const at = (day: number, hour: number, minute = 0) => new Date(2026, 2, day, hour, minute).toISOString();
const programs = [
  { id: 1, epg_channel_id: 42, title: 'Morning Show', start_time: at(25, 9), end_time: at(25, 10) },
  { id: 2, epg_channel_id: 42, title: 'Late Match', description: 'Knockout match', category: 'Sports', start_time: at(25, 11, 30), end_time: at(25, 12, 30) },
  { id: 3, epg_channel_id: 42, title: 'Evening News', start_time: at(25, 18), end_time: at(25, 19) },
  { id: 4, epg_channel_id: 42, title: 'Tomorrow Special', start_time: at(26, 8), end_time: at(26, 9) },
];

const renderView = () =>
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <ScheduleView epgChannelId={42} now={now} />
    </ThemeProvider>
  );

describe('ScheduleView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseEPGPrograms.mockReturnValue({ data: programs, isLoading: false, error: null });
  });

  it('shows now/next for today, counts the day and groups programmes by hour', () => {
    renderView();

    expect(screen.getByRole('tab', { name: 'Today', selected: true })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Tomorrow' })).toBeInTheDocument();
    expect(screen.getAllByRole('tab')).toHaveLength(7);

    const nowNext = screen.getByRole('region', { name: 'Now and next' });
    expect(within(nowNext).getByText('Late Match')).toBeInTheDocument();
    expect(within(nowNext).getByText(/11:30–12:30 · ends in/)).toBeInTheDocument();
    expect(within(nowNext).getByRole('progressbar', { name: 'Late Match progress' })).toHaveAttribute('aria-valuenow', '50');
    expect(within(nowNext).getByText('Evening News')).toBeInTheDocument();
    expect(within(nowNext).getByText(/18:00–19:00 · starts in/)).toBeInTheDocument();

    expect(screen.getByText('3 programmes today')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: '09:00' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: '11:00' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 3, name: '18:00' })).toBeInTheDocument();
    expect(screen.queryByText('Tomorrow Special')).not.toBeInTheDocument();
  });

  it('keeps descriptions collapsed until More is pressed', () => {
    renderView();
    const row = screen.getByRole('listitem', { name: 'Late Match' });
    const more = within(row).getByRole('button', { name: 'More' });
    expect(more).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(more);
    expect(within(row).getByRole('button', { name: 'Less' })).toHaveAttribute('aria-expanded', 'true');
    expect(within(row).getByText('Knockout match')).toBeVisible();
  });

  it('switches days, refetches around the chosen day and hides now/next', () => {
    renderView();
    fireEvent.click(screen.getByRole('tab', { name: 'Tomorrow' }));

    const lastCall = mockUseEPGPrograms.mock.calls.at(-1) as [number, string, string];
    expect(lastCall[0]).toBe(42);
    expect(new Date(lastCall[1]).getTime()).toBe(new Date(2026, 2, 25).getTime());
    expect(new Date(lastCall[2]).getTime()).toBe(new Date(2026, 2, 28).getTime());
    expect(screen.getByText('1 programme tomorrow')).toBeInTheDocument();
    expect(screen.getByText('Tomorrow Special')).toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Now and next' })).not.toBeInTheDocument();
  });

  it('shows loading, error and empty states', () => {
    mockUseEPGPrograms.mockReturnValue({ data: undefined, isLoading: true, error: null });
    const { unmount } = renderView();
    expect(screen.getByRole('status')).toHaveTextContent('Loading schedule…');
    unmount();

    mockUseEPGPrograms.mockReturnValue({ data: undefined, isLoading: false, error: new Error('boom') });
    const { unmount: unmountSecond } = renderView();
    expect(screen.getByText('Unable to load the schedule right now.')).toBeInTheDocument();
    unmountSecond();

    mockUseEPGPrograms.mockReturnValue({ data: [], isLoading: false, error: null });
    renderView();
    expect(screen.getByText('No programmes today.')).toBeInTheDocument();
    expect(screen.getByText('Nothing on air right now.')).toBeInTheDocument();
  });
});
