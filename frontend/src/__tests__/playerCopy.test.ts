import i18next from 'i18next';
import { ApiError } from '../services/apiErrors';
import { describePlayerError, describePlaySent, describeRemotePlayerError, describeRemotePlayerProbe } from '../components/player/playerCopy';

afterEach(async () => { await i18next.changeLanguage('en'); });

it('translates player reasons at render time while retaining programme, device and codec names', async () => {
  const status = { error: null, error_message: '', codecs: { video: 'mpeg2video' } };
  expect(describePlayerError(status, false)).toContain("Your browser can't play");
  await i18next.changeLanguage('es');
  expect(describePlayerError(status, false)).toContain('Tu navegador');
  expect(describePlayerError(status, false)).toContain('MPEG-2');
  const feedback = describePlaySent('BBC News', 'Living Room', ['localhost', 'tuner_blocked']);
  expect(feedback.severity).toBe('warning');
  expect(feedback.message).toContain('Se envió BBC News a Living Room.');
  expect(feedback.message).toContain('Conexiones');
  expect(feedback.message).not.toMatch(/It may not|Also,|Integrations/);
});

it('selects actionable Spanish probe guidance by reason rather than server sentences', async () => {
  await i18next.changeLanguage('es');
  const probe = { reachable: false, authenticated: false, version: null, message: 'Arbitrary diagnostic', hint: null, tuner_access: { addresses: [], allowed: true } };
  expect(describeRemotePlayerProbe({ ...probe, reason: 'not_player' }).text).toContain('tipo de reproductor');
  expect(describeRemotePlayerProbe({ ...probe, reason: 'no_password' }).text).toContain('Lua HTTP');
  expect(describeRemotePlayerProbe({ ...probe, reason: 'pairing_required' }).text).toContain('código nuevo');
  expect(describeRemotePlayerError(new ApiError({ status: 502, kind: 'server', canRetry: false, code: 'REMOTE_PLAYER_AUTH', message: 'Unrelated', context: { kind: 'wrong_password' } }))).toContain('Comprueba la contraseña');
});
