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
