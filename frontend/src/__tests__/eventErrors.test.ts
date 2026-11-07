import { ApiError } from '../services/apiErrors';
import { eventErrorMessage } from '../components/events/eventErrors';

it('shows safe validation locations and source conflicts instead of an opaque failure', () => {
  expect(eventErrorMessage(new ApiError({ status: 422, kind: 'validation', canRetry: false, message: 'Invalid', data: {
    detail: [{ loc: ['body', 'observations', 0, 'timezone'], msg: 'Use an IANA timezone', input: 'private input' }],
  } }))).toBe('body.observations.0.timezone: Use an IANA timezone');
  expect(eventErrorMessage(new ApiError({ status: 409, kind: 'unknown', canRetry: false, message: 'Schedule source changed; review it again' }))).toBe('Schedule source changed; review it again');
});
