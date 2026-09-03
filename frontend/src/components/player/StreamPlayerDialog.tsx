import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Snackbar,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import Hls from 'hls.js';
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
}

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
const StreamPlayerDialog: React.FC<StreamPlayerDialogProps> = ({ open, contentId, title, onClose, extraActions }) => {
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
  const [copied, setCopied] = useState<'ok' | 'failed' | null>(null);
  const leftRef = useRef(false);

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
    leftRef.current = false;
    sessionIdRef.current = null;
    setSessionId(null);
    start.mutate(contentId, {
      onSuccess: (session) => {
        sessionIdRef.current = session.id;
        setSessionId(session.id);
      },
      onError: (err) => {
        if (err.code === 'PLAYER_LIMIT_REACHED') {
          const limit = (err.context as { limit?: number } | undefined)?.limit;
          setStartError(
            `Too many channels are playing at once${limit ? ` (limit ${limit})` : ''}. Close another player and try again.`
          );
        } else {
          setStartError(getErrorMessage(err));
        }
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentId, leave]);

  useEffect(() => {
    if (open && contentId) startSession();
    return () => {
      leave();
      hlsRef.current?.destroy();
      hlsRef.current = null;
      attachedUrl.current = null;
      sessionIdRef.current = null;
      setSessionId(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, contentId]);

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
        }
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
    leave();
    onClose();
  };

  const gone = Boolean(statusError && statusError.status === 404);
  const problem = startError ?? (gone ? 'The stream ended.' : status ? describePlayerError(status, hlsCodecError) : null);
  const stats = status?.stats;
  const statusText =
    status?.state === 'ready'
      ? 'Playing'
      : status?.state === 'starting'
        ? `Starting… ${stats ? `${stats.peers} peers · ${formatBitrate(stats.speed_down * 8000)}` : 'contacting the engine'}`
        : start.isPending
          ? 'Starting…'
          : '';

  return (
    <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} maxWidth="md" fullWidth aria-labelledby="stream-player-title">
      <DialogTitle id="stream-player-title">{title}</DialogTitle>
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
                status?.error && status.error !== 'ffmpeg_missing' ? (
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
          {status?.codecs.video ? (
            <Typography variant="caption" color="text.secondary">
              Video {status.codecs.video.toUpperCase()} · audio {(status.codecs.audio ?? 'unknown').toUpperCase()} re-encoded to AAC
            </Typography>
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        {extraActions}
        <Button onClick={handleCopy} disabled={!streamLink}>
          Copy stream link
        </Button>
        <Button variant="contained" onClick={handleClose}>
          Close
        </Button>
      </DialogActions>
      <Snackbar open={copied !== null} autoHideDuration={3000} onClose={() => setCopied(null)}>
        <Alert severity={copied === 'ok' ? 'success' : 'error'} onClose={() => setCopied(null)}>
          {copied === 'ok' ? 'Stream link copied. Open it in VLC or any player on this network.' : 'Unable to copy the link.'}
        </Alert>
      </Snackbar>
    </Dialog>
  );
};

export default StreamPlayerDialog;
