import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Snackbar,
  MenuItem,
  TextField,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import Hls from 'hls.js';
import ExpandMoreRounded from '@mui/icons-material/ExpandMoreRounded';
import { usePlayerSessionStatus, useStartPlayerSession } from '../../hooks/usePlayer';
import { usePublicUrl } from '../../hooks/useSystemServices';
import { playerService } from '../../services/playerService';
import { getApiToken } from '../../services/apiToken';
import { buildPublicUrl } from '../../services/playlistService';
import { getErrorMessage } from '../../utils/errorUtils';
import { formatBitrate } from '../../utils/format';
import { describePlayerError } from './playerCopy';

export interface StreamPlayerDialogProps {
  open: boolean;
  contentId: string | null;
  title: string;
  onClose: () => void;
  /** Extra buttons (e.g. "Play on…") rendered next to Copy stream link. */
  extraActions?: React.ReactNode;
  details?: React.ReactNode;
  /** Embedded viewing surface used by Live TV. */
  inline?: boolean;
}

/** Fatal hls.js errors we try to ride out before telling the user. */
const MAX_RECOVERIES = 3;

const withToken = (url: string): string => {
  const token = getApiToken();
  if (!token) return url;
  return `${url}${url.includes('?') ? '&' : '?'}${new URLSearchParams({ token }).toString()}`;
};

/** Autoplay, retrying muted: browsers block autoplay with sound. */
const startPlayback = (video: HTMLVideoElement): void => {
  void Promise.resolve(video.play()).catch(() => {
    video.muted = true;
    void Promise.resolve(video.play()).catch(() => undefined);
  });
};

/** Plays one channel through the backend's HLS pipeline. */
const StreamPlayerDialog: React.FC<StreamPlayerDialogProps> = ({ open, contentId, title, onClose, extraActions, details, inline = false }) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const attachedUrl = useRef<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  // Mirrors sessionId so the release path stays a stable callback: the
  // open/contentId effect's cleanup would otherwise close over the id as it
  // was when the effect ran (null) and never release the session.
  const sessionIdRef = useRef<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [hlsCodecError, setHlsCodecError] = useState(false);
  const [playbackError, setPlaybackError] = useState<string | null>(null);
  // Bounded so a permanently broken stream surfaces instead of retrying forever.
  const recoveries = useRef(0);
  const [copied, setCopied] = useState<'ok' | 'failed' | null>(null);
  const leftRef = useRef(false);
  const requestGeneration = useRef(0);

  const [audioSelection, setAudioSelection] = useState<{ contentId: string | null; index: number | null }>({ contentId: null, index: null });
  const audioIndex = audioSelection.contentId === contentId ? audioSelection.index : null;
  const start = useStartPlayerSession();
  const { data: status, error: statusError } = usePlayerSessionStatus(sessionId);
  const { data: publicUrl } = usePublicUrl();

  const leave = useCallback(() => {
    const id = sessionIdRef.current;
    if (leftRef.current || !id) return;
    leftRef.current = true;
    playerService.leaveSession(id);
  }, []);

  const startSession = useCallback(() => {
    if (!contentId) return;
    // Retry after an error: release the session we are replacing first.
    leave();
    setStartError(null);
    setHlsCodecError(false);
    setPlaybackError(null);
    recoveries.current = 0;
    // Retry is a full restart: drop the old player so the next ready status
    // re-attaches even when the backend hands back the same session.
    hlsRef.current?.destroy();
    hlsRef.current = null;
    attachedUrl.current = null;
    leftRef.current = false;
    sessionIdRef.current = null;
    setSessionId(null);
    const generation = ++requestGeneration.current;
    // Promise handlers also run after unmount; stale starts must release their viewer.
    void start.mutateAsync(audioIndex === null ? contentId : { contentId, audioIndex }).then((session) => {
        if (generation !== requestGeneration.current) {
          playerService.leaveSession(session.id);
          return;
        }
        sessionIdRef.current = session.id;
        setSessionId(session.id);
      }, (err) => {
        if (generation !== requestGeneration.current) return;
        if (err.code === 'PLAYER_LIMIT_REACHED') {
          const limit = (err.context as { limit?: number } | undefined)?.limit;
          setStartError(
            `Too many channels are playing at once${limit ? ` (limit ${limit})` : ''}. Close another player and try again.`
          );
        } else {
          setStartError(getErrorMessage(err));
        }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentId, audioIndex, leave]);

  useEffect(() => {
    if (open && contentId) startSession();
    const video = videoRef.current;
    return () => {
      requestGeneration.current += 1;
      leave();
      hlsRef.current?.destroy();
      hlsRef.current = null;
      attachedUrl.current = null;
      if (video) {
        video.pause();
        video.removeAttribute('src');
        video.load();
      }
      sessionIdRef.current = null;
      setSessionId(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, contentId, audioIndex]);

  useEffect(() => {
    const onPageHide = () => leave();
    window.addEventListener('pagehide', onPageHide);
    return () => window.removeEventListener('pagehide', onPageHide);
  }, [leave]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !status || !status.hls_ready || attachedUrl.current === status.playlist_url) return;
    attachedUrl.current = status.playlist_url;
    hlsRef.current?.destroy();
    hlsRef.current = null;
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        liveSyncDurationCount: 3,
        xhrSetup: (xhr) => {
          const token = getApiToken();
          if (token) xhr.setRequestHeader('X-Api-Token', token);
        },
      });
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (
          data.details === Hls.ErrorDetails.BUFFER_INCOMPATIBLE_CODECS_ERROR ||
          data.details === Hls.ErrorDetails.BUFFER_ADD_CODEC_ERROR
        ) {
          setHlsCodecError(true);
          return;
        }
        if (!data.fatal) return;
        // hls.js recovers nothing fatal on its own: unhandled, the video
        // freezes for good while the strip still reads "Playing".
        recoveries.current += 1;
        if (recoveries.current <= MAX_RECOVERIES && data.type === Hls.ErrorTypes.NETWORK_ERROR) {
          hls.startLoad();
          return;
        }
        if (recoveries.current <= MAX_RECOVERIES && data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          hls.recoverMediaError();
          return;
        }
        hls.destroy();
        if (hlsRef.current === hls) hlsRef.current = null;
        setPlaybackError('Playback stopped in your browser. Try again.');
      });
      hls.loadSource(status.playlist_url);
      hls.attachMedia(video);
      hlsRef.current = hls;
    } else {
      // Safari and iOS play HLS natively but cannot send headers.
      video.src = withToken(status.playlist_url);
    }
    startPlayback(video);
  }, [status]);

  const streamLink = contentId ? buildPublicUrl(`/tuner/stream/${contentId}.ts`, publicUrl?.url) : '';
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(streamLink);
      setCopied('ok');
    } catch {
      setCopied('failed');
    }
  };

  const handleClose = () => {
    requestGeneration.current += 1;
    leave();
    onClose();
  };

  const gone = Boolean(statusError && statusError.status === 404);
  const backendProblem = gone ? 'The stream ended.' : status ? describePlayerError(status, hlsCodecError) : null;
  const problem = startError ?? backendProblem ?? playbackError;
  const stats = status?.stats;
  const statusText =
    status?.state === 'ready'
      ? 'Playing'
      : status?.state === 'starting'
        ? `Starting… ${stats ? `${stats.peers} peers · ${formatBitrate(stats.speed_down * 8000)}` : 'contacting the engine'}`
        : start.isPending
          ? 'Starting…'
          : '';

  const playbackOptions = <>
          {status?.codecs.video ? (
            <Typography variant="caption" color="text.secondary">
              Video {status.codecs.video.toUpperCase()} · audio {(status.codecs.audio ?? 'unknown').toUpperCase()} re-encoded to AAC
            </Typography>
          ) : null}
          {status?.audio_tracks?.length ? <TextField select fullWidth label="Audio track" value={audioIndex ?? 'default'}
            onChange={(event) => setAudioSelection({ contentId, index: event.target.value === 'default' ? null : Number(event.target.value) })}
            helperText="Changing audio restarts your playback. Other viewers keep their selected track.">
            <MenuItem value="default">Default audio</MenuItem>
            {status.audio_tracks.map((track) => <MenuItem key={track.index} value={track.index} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere' }}>
              {`Track ${track.index + 1}${track.language ? ` · ${track.language}` : ''}${track.title ? ` · ${track.title}` : ''}${track.codec ? ` · ${track.codec.toUpperCase()}` : ''}${track.channel_layout ? ` · ${track.channel_layout}` : ''}`}
            </MenuItem>)}
          </TextField> : null}
          {details}
  </>;

  const playerContent = (
    <>
      <DialogTitle id="stream-player-title" sx={{ overflowWrap: 'anywhere', ...(inline ? { px: 2, py: 1, fontSize: '1.1rem' } : {}) }}>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={1.5}>
          <Box sx={{ position: 'relative', width: '100%', aspectRatio: '16 / 9', backgroundColor: '#000', borderRadius: 1, overflow: 'hidden' }}>
            {/* eslint-disable-next-line jsx-a11y/media-has-caption -- live AceStream streams carry no caption track */}
            <video ref={videoRef} controls autoPlay playsInline style={{ width: '100%', height: '100%' }} aria-label={`Video player for ${title}`} />
          </Box>
          {problem ? (
            <Alert
              severity={status?.error === 'ffmpeg_missing' ? 'warning' : 'error'}
              action={
                status?.error !== 'ffmpeg_missing' ? (
                  <Button color="inherit" size="small" onClick={startSession}>
                    Retry
                  </Button>
                ) : undefined
              }
            >
              {problem}
            </Alert>
          ) : (
            <Typography role="status" aria-live="polite" variant="body2" color="text.secondary">
              {statusText}
            </Typography>
          )}
          {inline ? <Accordion disableGutters><AccordionSummary expandIcon={<ExpandMoreRounded />}><Typography>Playback options and schedule</Typography></AccordionSummary><AccordionDetails><Stack spacing={1.5}>{playbackOptions}</Stack></AccordionDetails></Accordion> : playbackOptions}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ flexWrap: 'wrap', gap: 1, px: 2, pb: 'max(16px, env(safe-area-inset-bottom))' }}>
        {extraActions}
        <Button onClick={handleCopy} disabled={!streamLink}>
          Copy stream link
        </Button>
        <Button variant="contained" onClick={handleClose}>
          {inline ? 'Stop watching' : 'Close'}
        </Button>
      </DialogActions>
      <Snackbar open={copied !== null} autoHideDuration={3000} onClose={() => setCopied(null)}>
        <Alert severity={copied === 'ok' ? 'success' : 'error'} onClose={() => setCopied(null)}>
          {copied === 'ok' ? 'Stream link copied. Open it in VLC or any player on this network.' : 'Unable to copy the link.'}
        </Alert>
      </Snackbar>
    </>
  );

  if (inline) return open ? <Box component="section" aria-label="Live TV player" sx={{ minWidth: 0, bgcolor: 'background.paper', border: 1, borderColor: 'divider', borderRadius: 2 }}>{playerContent}</Box> : null;
  return <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} maxWidth="md" fullWidth aria-labelledby="stream-player-title">{playerContent}</Dialog>;
};

export default StreamPlayerDialog;
