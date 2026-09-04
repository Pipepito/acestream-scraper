import type { ApiError } from '../../services/apiErrors';
import type { PlayerCodecs, PlayerError } from '../../services/playerService';
import type { RemotePlayerProbe } from '../../services/remotePlayerService';

/** How a page reports a player action's outcome. A send can succeed and still
 * warn: the player took the link but probably cannot fetch it. */
export type PlayerNotify = (message: string, severity: 'success' | 'warning' | 'error') => void;

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
      return "This server can't prepare streams for the browser. Open the channel in VLC instead.";
    case 'engine_stalled':
      return 'No one is sharing this channel right now. Try again later or pick another stream.';
    case 'ffmpeg_failed':
      return 'The stream stopped unexpectedly. Try again.';
    case 'engine_refused':
    case 'engine_unavailable':
      return `The AceStream engine could not start this channel: ${status.error_message || 'no details'}.`;
    default:
      break;
  }
  const codecName = UNPLAYABLE_VIDEO[(status.codecs.video ?? '').toLowerCase()];
  if (codecName) {
    return `Your browser can't play this channel's video format (${codecName}). Send it to VLC or Kodi instead.`;
  }
  if (hlsCodecError) {
    return "Your browser can't play this channel's video format. Send it to VLC or Kodi instead.";
  }
  return null;
};

/** Guided copy for remote-player failures; never the API-token notice (that is a 401, these are 502/400). */
export const describeRemotePlayerError = (error: ApiError): string => {
  if (error.code === 'REMOTE_PLAYER_AUTH') {
    const kind = (error.context as { kind?: string } | undefined)?.kind;
    return kind === 'no_password'
      ? "VLC's web interface has no password. In VLC: Tools > Preferences > All > Interface > Main interfaces > Web, then Lua > Lua HTTP > Password."
      : 'Check the password (VLC: Lua HTTP password; Kodi: Settings > Services > Control).';
  }
  if (error.code === 'REMOTE_PLAYER_UNREACHABLE') return 'The player did not answer. Is it running with its web interface on?';
  if (error.code === 'REMOTE_PLAYER_COMMAND_FAILED') return `The player refused the command: ${error.message}`;
  return error.message || 'Something went wrong talking to the player.';
};

/**
 * Why a channel the player accepted probably will not start, in the same codes
 * the public address section already renders (`POST /remote-players/{id}/play`
 * returns them alongside the URL it sent).
 */
const PLAY_WARNING_TEXT: Record<string, string> = {
  localhost:
    'the link points at localhost, which on the player means the player itself. Set the public address under Integrations to this server\u2019s network address.',
  'docker-internal':
    'the link points at a Docker-internal address other devices cannot reach. Set the public address under Integrations to this server\u2019s network address.',
  tuner_blocked:
    'this player\u2019s address is not allowed to fetch streams from this server, so it will be refused. Add its network to the allowed list, or give the player a stream link format that points at the engine or Acexy.',
};

export interface PlaySentFeedback {
  message: string;
  severity: 'success' | 'warning';
}

/** What to tell the user after a player accepted a channel: plain confirmation,
 * or a warning when the server says the link will not reach it. */
export const describePlaySent = (title: string, playerName: string, warnings?: string[]): PlaySentFeedback => {
  const sent = `Sent ${title} to ${playerName}.`;
  const reasons = (warnings ?? []).map((code) => PLAY_WARNING_TEXT[code]).filter(Boolean);
  return reasons.length === 0
    ? { message: sent, severity: 'success' }
    : { message: `${sent} It may not start: ${reasons.join(' Also, ')}`, severity: 'warning' };
};

/** One "Test connection" outcome, so the card and the dialog say the same thing. */
export interface ProbeVerdict {
  severity: 'success' | 'warning' | 'error';
  text: string;
}

/** The verdict for one remote-player probe: reachable, authenticated, and able to fetch our stream links. */
export const describeRemotePlayerProbe = (probe: RemotePlayerProbe): ProbeVerdict => {
  if (!probe.reachable) return { severity: 'error', text: `${probe.message} ${probe.hint ?? ''}`.trim() };
  if (!probe.authenticated) return { severity: 'warning', text: probe.hint ?? probe.message };
  const access = probe.tuner_access.allowed
    ? ''
    : ` This player (${probe.tuner_access.addresses.join(', ')}) is outside TUNER_ALLOWED_NETWORKS and will get 403 from the stream link: add its network or choose a stream link format that points at the engine or Acexy.`;
  return {
    severity: probe.tuner_access.allowed ? 'success' : 'warning',
    text: `Connected${probe.version ? ` (version ${probe.version})` : ''}.${access}`,
  };
};
