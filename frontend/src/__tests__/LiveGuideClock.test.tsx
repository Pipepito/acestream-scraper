import React from 'react';
import { act, render, screen, within } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import ScheduleView from '../components/epg/ScheduleView';
import { createAppTheme } from '../theme';
const mockPrograms = jest.fn();
jest.mock('../hooks/useEPG', () => ({ useEPGPrograms: () => mockPrograms() }));

it('advances on-air state without interaction and compares explicit offsets as instants', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2026-10-25T01:59:45Z'));
  mockPrograms.mockReturnValue({ data: [
    { id: 1, title: 'Before change', start_time: '2026-10-25T02:30:00+02:00', end_time: '2026-10-25T03:00:00+01:00' },
    { id: 2, title: 'After change', start_time: '2026-10-25T03:00:00+01:00', end_time: '2026-10-25T04:00:00+01:00' },
  ] });
  const { unmount } = render(<ThemeProvider theme={createAppTheme('light')}><ScheduleView epgChannelId={1} /></ThemeProvider>);
  const region = screen.getByRole('region', { name: 'Now and next' });
  expect(within(region).getByRole('progressbar', { name: 'Before change progress' })).toBeInTheDocument();
  act(() => jest.advanceTimersByTime(30_000));
  expect(within(region).getByRole('progressbar', { name: 'After change progress' })).toBeInTheDocument();
  unmount();
  jest.useRealTimers();
});
