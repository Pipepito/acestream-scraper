import { ApiError } from '../services/apiErrors';
import { eventErrorMessage } from '../components/events/eventErrors';

it('shows safe validation locations and source conflicts instead of an opaque failure', () => {
  expect(eventErrorMessage(new ApiError({ status: 422, kind: 'validation', canRetry: false, message: 'Invalid', data: {
    detail: [{ loc: ['body', 'observations', 0, 'timezone'], msg: 'Use an IANA timezone', input: 'private input' }],
  } }))).toBe('body.observations.0.timezone: Use an IANA timezone');
  expect(eventErrorMessage(new ApiError({ status: 409, kind: 'unknown', canRetry: false, message: 'Schedule source changed; review it again' }))).toBe('Schedule source changed; review it again');
});

it('translates stable validation reasons in Spanish and excludes private input/context', async () => {
  const { default: i18next } = await import('i18next');
  await i18next.changeLanguage('es');
  try {
    const result = eventErrorMessage(new ApiError({ status: 422, kind: 'validation', canRetry: false, message: 'Invalid', data: {
      detail: [
        { loc: ['body', 'observations', 0, 'timezone'], type: 'EVENT_TIMEZONE_INVALID', msg: 'Use an IANA timezone', input: 'private-secret', ctx: { secret: 'private-context' } },
        { loc: ['body', 'observations', 1, 'title'], type: 'missing', msg: 'Field required' },
      ],
    } }));
    expect(result).toContain('Fila 1');
    expect(result).toContain('zona horaria');
    expect(result).toContain('Fila 2');
    expect(result).not.toMatch(/private-|Use an IANA|Field required/);
  } finally { await i18next.changeLanguage('en'); }
});
