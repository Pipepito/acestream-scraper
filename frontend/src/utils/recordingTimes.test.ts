import { localRecordingTime, recordingTimeChoices } from './recordingTimes';

test('requires an explicit choice for the repeated Madrid hour', () => {
  expect(recordingTimeChoices('2026-10-25T02:30', 'Europe/Madrid')).toEqual([
    '2026-10-25T00:30:00.000Z', '2026-10-25T01:30:00.000Z',
  ]);
});

test('rejects nonexistent local times and invalid zones', () => {
  expect(recordingTimeChoices('2026-03-29T02:30', 'Europe/Madrid')).toEqual([]);
  expect(recordingTimeChoices('2026-10-28T12:00', 'Invalid/Zone')).toEqual([]);
  expect(recordingTimeChoices('2026-02-30T12:00', 'UTC')).toEqual([]);
});

test('uses the selected timezone rather than the browser timezone', () => {
  expect(localRecordingTime(new Date('2026-10-28T10:00:00Z'), 'Asia/Kathmandu')).toBe('2026-10-28T15:45');
  expect(recordingTimeChoices('2026-10-28T15:45', 'Asia/Kathmandu')).toEqual(['2026-10-28T10:00:00.000Z']);
});
