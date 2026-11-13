import { uiText } from '../../i18n/text';
import { getErrorMessage } from '../../utils/errorUtils';
import { ApiError } from '../../services/apiErrors';
import type { PlayerCodecs, PlayerError } from '../../services/playerService';
import type { RemotePlayerProbe } from '../../services/remotePlayerService';

/** How a page reports a player action's outcome. A send can succeed and still
 * warn: the player took the link but probably cannot fetch it. */
export type PlayerNotify = (message: string | (() => string), severity: 'success' | 'warning' | 'error') => void;

export interface PlayerErrorInput {
  error: PlayerError | null;
  error_message: string;
  codecs: PlayerCodecs;
}

/**
 * Video codecs no browser plays natively, mapped to the name a user would
 * recognise. ffmpeg copies the video track, so these reach the browser as-is.
 */
const UNPLAYABLE_VIDEO: Record<string, string> = {
  mpeg2video: 'MPEG-2',
  mpeg1video: 'MPEG-1',
  vc1: 'VC-1',
  msmpeg4v3: 'MPEG-4 v3',
};

/** Plain-language explanation for the player status strip; null when nothing is wrong. */
export const describePlayerError = (status: PlayerErrorInput, hlsCodecError: boolean): string | null => {
  switch (status.error) {
    case 'ffmpeg_missing':
      return uiText("This server can't prepare streams for the browser. Open the channel in VLC instead.");
    case 'source_unavailable':
      return uiText("The HTTP stream could not be opened. Retry or choose another stream.");
    case 'engine_stalled':
      return uiText("The stream did not become ready in time. Check the engine or proxy, retry, or pick another stream.");
    case 'ffmpeg_failed':
      return uiText("The stream stopped unexpectedly. Try again.");
    case 'engine_refused':
    case 'engine_unavailable':
      return uiText("The AceStream engine could not start this channel: {{details}}.", { details: status.error_message || uiText("no details") });
    default:
      break;
  }
  const codecName = UNPLAYABLE_VIDEO[(status.codecs.video ?? '').toLowerCase()];
  if (codecName) {
    return uiText("Your browser can't play this channel's video format ({{codec}}). Send it to VLC or Kodi instead.", { codec: codecName });
  }
  if (hlsCodecError) {
    return uiText("Your browser can't play this channel's video format. Send it to VLC or Kodi instead.");
  }
  return null;
};

/** Guided copy for remote-player failures; never the API-token notice (that is a 401, these are 502/400). */
export const describeRemotePlayerError = (error: ApiError): string => {
  if (error.code === 'REMOTE_PLAYER_AUTH') {
    const kind = (error.context as { kind?: string } | undefined)?.kind;
    if (kind === 'pairing_required') return uiText("Pair VLC Android again in Connections → Remote players. Request a new code if the previous one has expired.");
    return kind === 'no_password'
      ? uiText("VLC's web interface has no password. In VLC: Tools > Preferences > All > Interface > Main interfaces > Web, then Lua > Lua HTTP > Password.")
      : uiText("Check the password (VLC: Lua HTTP password; Kodi: Settings > Services > Control).");
  }
  if (error.code === 'REMOTE_PLAYER_UNREACHABLE') return uiText("The player did not answer. Is it running with its web interface on?");
  if (error.code === 'REMOTE_PLAYER_COMMAND_FAILED') return uiText("The player refused the command: {{details}}", { details: error.message });
  return getErrorMessage(error);
};

/**
 * Why a channel the player accepted probably will not start, in the same codes
 * the public address section already renders (`POST /remote-players/{id}/play`
 * returns them alongside the URL it sent).
 */
const playWarningText = (code: string): string | undefined => {
  switch (code) {
    case "localhost": return uiText("the link points at localhost, which on the player means the player itself. Set the public address under Connections to this server’s network address.");
    case "docker-internal": return uiText("the link points at a Docker-internal address other devices cannot reach. Set the public address under Connections to this server’s network address.");
    case "tuner_blocked": return uiText("this player’s address is not allowed to fetch streams from this server, so it will be refused. Add its network to the allowed list, or give the player a stream link format that points at the engine or Acexy.");
    default: return undefined;
  }
};

export interface PlaySentFeedback {
  message: string;
  severity: 'success' | 'warning';
}

/** What to tell the user after a player accepted a channel: plain confirmation,
 * or a warning when the server says the link will not reach it. */
export const describePlaySent = (title: string, playerName: string, warnings?: string[]): PlaySentFeedback => {
  const sent = uiText("Sent {{title}} to {{player}}.", { title, player: playerName });
  const reasons = (warnings ?? []).map(playWarningText).filter(Boolean);
  return reasons.length === 0
    ? { message: sent, severity: 'success' }
    : { message: uiText("{{sent}} It may not start: {{reasons}}", { sent, reasons: reasons.join(uiText(" Also, ")) }), severity: 'warning' };
};

/** One "Test connection" outcome, so the card and the dialog say the same thing. */
export interface ProbeVerdict {
  severity: 'success' | 'warning' | 'error';
  text: string;
}

/** The verdict for one remote-player probe: reachable, authenticated, and able to fetch our stream links. */
export const describeRemotePlayerProbe = (probe: RemotePlayerProbe): ProbeVerdict => {
  if (probe.reason === 'not_player') return { severity: 'error', text: uiText("The address answered, but it is not the selected player. Check the player type, host and port.") };
  if (probe.reason === 'no_password' || probe.reason === 'wrong_password' || probe.reason === 'pairing_required') return { severity: 'warning', text: describeRemotePlayerError(new ApiError({ status: 400, kind: 'validation', canRetry: false, code: 'REMOTE_PLAYER_AUTH', message: probe.message, context: { kind: probe.reason } })) };
  if (!probe.reachable) return { severity: 'error', text: uiText("The player did not answer. Is it running with its web interface on?") };
  if (!probe.authenticated) return { severity: 'warning', text: uiText("The player answered but did not accept the credentials. Check its password or pair it again.") };
  const connected = probe.version ? uiText("Connected (version {{version}}).", { version: probe.version }) : uiText("Connected.");
  const access = probe.tuner_access.allowed ? '' : uiText("This player ({{addresses}}) is outside TUNER_ALLOWED_NETWORKS and will get 403 from the stream link: add its network or choose a stream link format that points at the engine or Acexy.", { addresses: probe.tuner_access.addresses.join(', ') });
  return {
    severity: probe.tuner_access.allowed ? 'success' : 'warning',
    text: [connected, access].filter(Boolean).join(' '),
  };
};

/** Keep the admission reason and numeric capacity separate from server wording. */
export function describePlayerStartError(error: unknown): string {
  if (error && typeof error === 'object' && 'code' in error && error.code === 'PLAYER_LIMIT_REACHED') {
    const context = 'context' in error ? error.context : null;
    const limit = context && typeof context === 'object' && 'limit' in context ? context.limit : null;
    return typeof limit === 'number' && Number.isFinite(limit) && limit > 0
      ? uiText('Too many channels are playing at once (limit {{limit}}). Close another player and try again.', { limit })
      : uiText('Too many channels are playing at once. Close another player and try again.');
  }
  return getErrorMessage(error);
}
