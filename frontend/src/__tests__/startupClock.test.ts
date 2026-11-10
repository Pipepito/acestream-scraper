import { startupClockSample } from '../utils/startupClock';

const start = Date.parse('2026-11-09T12:00:00Z');

it.each([600000, -600000, 300000, -300000, 0])('measures either direction: %s', offset => {
  const result = startupClockSample(new Date(start + 100 + offset).toISOString(), start, start + 200, 200);
  expect(result?.differenceMs).toBe(offset);
});

it('compares instants independently of timezone', () => {
  expect(startupClockSample('2026-11-09T13:00:00+01:00', start, start, 0)?.differenceMs).toBe(0);
});

it.each([undefined, null, '', 'not a date', '2026-11-09T12:00:00'])('rejects missing or ambiguous timestamp %s', timestamp => {
  expect(startupClockSample(timestamp, start, start, 0)).toBeUndefined();
});

it('rejects slow requests and browser clock changes', () => {
  const server = new Date(start).toISOString();
  expect(startupClockSample(server, start, start + 5001, 5001)).toBeUndefined();
  expect(startupClockSample(server, start, start + 600000, 100)).toBeUndefined();
  expect(startupClockSample(server, start, start - 600000, 100)).toBeUndefined();
  expect(startupClockSample(server, start, start, NaN)).toBeUndefined();
});
