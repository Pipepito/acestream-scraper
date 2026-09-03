import type { ApiError } from '../../services/apiErrors';
import type { PlayerCodecs, PlayerError } from '../../services/playerService';

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
