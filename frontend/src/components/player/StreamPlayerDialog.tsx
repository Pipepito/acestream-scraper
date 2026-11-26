import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
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
import type Hls from 'hls.js';
import { loadHls } from './loadHls';
import ExpandMoreRounded from '@mui/icons-material/ExpandMoreRounded';
import { usePlayerSessionStatus, useStartPlayerSession } from '../../hooks/usePlayer';
import { usePublicUrl } from '../../hooks/useSystemServices';
import { playerService } from '../../services/playerService';
import { getApiToken } from '../../services/apiToken';
import { accessSession } from '../../services/accessSession';
import { buildPublicUrl } from '../../services/playlistService';
import { formatBitrate } from '../../utils/format';
import { describePlayerStartError, describePlayerError } from './playerCopy';
import CastControls from './CastControls';
import { useAccess } from '../access/AccessContext';

export interface StreamPlayerDialogProps {
  open: boolean;
  contentId: string | null;
  title: string;
  onClose: () => void;
  /** Extra buttons (e.g. "Play on…") rendered next to Copy stream link. */
  extraActions?: React.ReactNode;
  details?: React.ReactNode;
  schedule?: React.ReactNode;
  /** The playing channel's streams, shown right under the status line so switching source is one click. */
  sources?: React.ReactNode;
  largePlayer?: boolean;
  onTogglePlayerSize?: () => void;
  /** Embedded viewing surface used by Live TV. */
  inline?: boolean;
}

/** Fatal hls.js errors we try to ride out before telling the user. */
const MAX_RECOVERIES = 3;

const withToken = (url: string): string => {
  if (accessSession.managed()) return url;
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
const StreamPlayerDialog: React.FC<StreamPlayerDialogProps> = ({ open, contentId, title, onClose, extraActions, details, schedule, sources, largePlayer, onTogglePlayerSize, inline = false }) => {
  const tUi = useUiText();
  const access = useAccess();
  const canManage = !access || access.status.mode === 'open' || Boolean(access.status.user?.administrator);
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
  const [startError, setStartError] = useState<unknown>(null);
  const [hlsConstructor, setHlsConstructor] = useState<typeof Hls | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [hlsCodecError, setHlsCodecError] = useState(false);
  const [playbackError, setPlaybackError] = useState<'stopped' | 'load' | null>(null);
  const [mediaState, setMediaState] = useState<'buffering' | 'playing' | 'paused'>('buffering');
  // Bounded so a permanently broken stream surfaces instead of retrying forever.
  const recoveries = useRef(0);
  const [copied, setCopied] = useState<'ok' | 'failed' | null>(null);
  const leftRef = useRef(false);
  const requestGeneration = useRef(0);

  const [audioSelection, setAudioSelection] = useState<{ contentId: string | null; index: number | null }>({ contentId: null, index: null });
  const [subtitleSelection, setSubtitleSelection] = useState<{ contentId: string | null; index: number | null }>({ contentId: null, index: null });
  const subtitleIndex = subtitleSelection.contentId === contentId ? subtitleSelection.index : null;
  const audioIndex = audioSelection.contentId === contentId ? audioSelection.index : null;
  const start = useStartPlayerSession();
  const { data: status, error: statusError } = usePlayerSessionStatus(sessionId);
  const { data: publicUrl } = usePublicUrl({ enabled: canManage });

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
    setLoadAttempt(attempt => attempt + 1);
    setHlsCodecError(false);
    setPlaybackError(null);
    setMediaState('buffering');
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
    void start.mutateAsync(audioIndex === null && subtitleIndex === null ? contentId : { contentId, ...(audioIndex !== null ? { audioIndex } : {}), ...(subtitleIndex !== null ? { subtitleIndex } : {}) }).then((session) => {
        if (generation !== requestGeneration.current) {
          playerService.leaveSession(session.id);
          return;
        }
        sessionIdRef.current = session.id;
        setSessionId(session.id);
      }, (err) => {
        if (generation !== requestGeneration.current) return;
        setStartError(err);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentId, audioIndex, subtitleIndex, leave]);

  useEffect(() => {
    if (!open || hlsConstructor) return;
    let cancelled = false;
    void loadHls().then(constructor => { if (!cancelled) setHlsConstructor(() => constructor); },
      () => { if (!cancelled) setPlaybackError('load'); });
    return () => { cancelled = true; };
  }, [open, hlsConstructor, loadAttempt]);

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
  }, [open, contentId, audioIndex, subtitleIndex]);

  useEffect(() => {
    const onPageHide = () => leave();
    window.addEventListener('pagehide', onPageHide);
    return () => window.removeEventListener('pagehide', onPageHide);
  }, [leave]);

  useEffect(() => {
    const video = videoRef.current;
    if (status?.state === 'error' || status?.state === 'stopped' || statusError?.status === 404) {
      hlsRef.current?.destroy();
      hlsRef.current = null;
      attachedUrl.current = null;
      if (video) {
        video.pause();
        video.removeAttribute('src');
        video.load();
      }
      return;
    }
    if (!video || !status || !status.hls_ready || !hlsConstructor || attachedUrl.current === status.playlist_url) return;
    const Hls = hlsConstructor;
    attachedUrl.current = status.playlist_url;
    hlsRef.current?.destroy();
    hlsRef.current = null;
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        liveSyncDurationCount: 3,
        xhrSetup: (xhr) => {
          const token = accessSession.managed() ? null : getApiToken();
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
        setPlaybackError('stopped');
      });
      hls.on(Hls.Events.SUBTITLE_TRACKS_UPDATED, () => {
        hls.subtitleTrack = status.subtitle_index != null ? 0 : -1;
        hls.subtitleDisplay = status.subtitle_index != null;
      });
      hls.loadSource(status.playlist_url);
      hls.attachMedia(video);
      hlsRef.current = hls;
    } else {
      // Safari and iOS play HLS natively but cannot send headers.
      video.src = withToken(status.playlist_url);
    }
    startPlayback(video);
  }, [status, statusError, hlsConstructor]);

  const isHttpStream = contentId?.startsWith('url:') ?? false;
  const streamLink = contentId && !isHttpStream ? buildPublicUrl(`/tuner/stream/${contentId}.ts`, publicUrl?.url) : '';
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
  const backendProblem = gone ? uiText("The stream ended.") : statusError ? uiText("Could not check the stream status. Check your connection and access token, then retry.") : status ? describePlayerError(status, hlsCodecError) : null;
  const problem = startError ? describePlayerStartError(startError) : backendProblem ?? (playbackError === 'load' ? tUi('The browser player could not load. Check your connection and try again.') : playbackError === 'stopped' ? tUi('Playback stopped in your browser. Try again.') : null);
  const stats = status?.stats;
  const statusText =
    status?.state === 'ready'
      ? mediaState === 'playing' ? uiText("Playing") : mediaState === 'paused' ? uiText("Paused") : uiText("Buffering…")
      : status?.state === 'starting'
        ? tUi('Starting… {{details}}', { details: stats ? tUi('{{count}} peers · {{rate}}', { count: stats.peers, rate: formatBitrate(stats.speed_down * 8000) }) : isHttpStream ? uiText('opening the HTTP stream') : tUi('contacting the engine') })
        : start.isPending
          ? uiText("Starting…")
          : '';

  const playbackOptions = <>
          {onTogglePlayerSize ? <Button onClick={onTogglePlayerSize} aria-pressed={largePlayer}>{largePlayer ? tUi("Standard player") : tUi("Larger player")}</Button> : null}
          {status?.codecs.video ? (
            <Typography variant="caption" color="text.secondary">
              {tUi("Video")}{' '}{status.codecs.video.toUpperCase()} {' '}{tUi("· audio")}{' '}{(status.codecs.audio ?? 'unknown').toUpperCase()} {tUi("re-encoded to AAC")}</Typography>
          ) : null}
          {status?.audio_tracks?.length ? <TextField select fullWidth label={tUi("Audio track")} value={audioIndex ?? 'default'}
            onChange={(event) => setAudioSelection({ contentId, index: event.target.value === 'default' ? null : Number(event.target.value) })}
            helperText={tUi("Changing audio restarts your playback. Other viewers keep their selected track.")}>
            <MenuItem value="default">{tUi("Default audio")}</MenuItem>
            {status.audio_tracks.map((track) => <MenuItem key={track.index} value={track.index} sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere' }}>
              {tUi("Track {{value0}}{{value1}}{{value2}}{{value3}}{{value4}}", { value0: track.index + 1, value1: track.language ? ` · ${track.language}` : '', value2: track.title ? ` · ${track.title}` : '', value3: track.codec ? ` · ${track.codec.toUpperCase()}` : '', value4: track.channel_layout ? ` · ${track.channel_layout}` : '' })}
            </MenuItem>)}
          </TextField> : null}
          {status?.subtitle_tracks?.length ? <TextField select fullWidth label={tUi("Subtitles")} value={subtitleIndex ?? 'off'}
            onChange={(event) => setSubtitleSelection({ contentId, index: event.target.value === 'off' ? null : Number(event.target.value) })}
            helperText={tUi("Changing subtitles restarts your playback. Other viewers keep their selected track.")}>
            <MenuItem value="off">{tUi("Off")}</MenuItem>
            {status.subtitle_tracks.map((track) => <MenuItem key={track.index} value={track.index} disabled={!track.supported}
              sx={{ whiteSpace: 'normal', overflowWrap: 'anywhere' }}>
              {tUi("Track {{value0}}{{value1}}{{value2}}{{value3}}", { value0: track.index + 1, value1: track.language ? ` · ${track.language}` : '', value2: track.codec ? ` · ${track.codec.toUpperCase()}` : '', value3: track.supported ? '' : ' · not supported in the browser' })}
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
            {/* eslint-disable-next-line jsx-a11y/media-has-caption -- available live subtitles are attached through HLS */}
            <video ref={videoRef} controls autoPlay playsInline
              onPlaying={() => setMediaState('playing')} onWaiting={() => setMediaState('buffering')} onPause={() => setMediaState('paused')} style={{ width: '100%', height: '100%' }} aria-label={tUi("Video player for {{value0}}", { value0: title })} />
          </Box>
          {problem ? (
            <Alert
              severity={status?.error === 'ffmpeg_missing' ? 'warning' : 'error'}
              action={
                status?.error !== 'ffmpeg_missing' ? (
                  <Button color="inherit" size="small" onClick={startSession}>
                    {tUi("Retry")}</Button>
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
          {sources}
          {inline ? <Accordion disableGutters><AccordionSummary expandIcon={<ExpandMoreRounded />}><Typography>{tUi("Playback options")}</Typography></AccordionSummary><AccordionDetails><Stack spacing={1.5}>{playbackOptions}</Stack></AccordionDetails></Accordion> : playbackOptions}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ flexWrap: 'wrap', gap: 1, px: 2, pb: 'max(16px, env(safe-area-inset-bottom))' }}>
        {extraActions}
        {access && contentId && open ? <CastControls contentId={contentId} audioIndex={audioIndex} subtitleIndex={subtitleIndex} /> : null}
        {!isHttpStream && canManage && access?.status.mode !== 'accounts' ? <Button onClick={handleCopy} disabled={!streamLink}>
          {tUi("Copy stream link")}</Button> : null}
        <Button variant="contained" onClick={handleClose}>
          {inline ? tUi("Stop watching") : tUi("Close")}
        </Button>
      </DialogActions>
      {schedule ? <Accordion defaultExpanded disableGutters sx={{ mx: 2, mb: 2 }}><AccordionSummary expandIcon={<ExpandMoreRounded />}><Typography component="h3">{tUi("Schedule")}</Typography></AccordionSummary><AccordionDetails sx={{ maxHeight: 420, overflowY: 'auto' }} tabIndex={0} aria-label={tUi("Channel schedule")}>{schedule}</AccordionDetails></Accordion> : null}
      <Snackbar open={copied !== null} autoHideDuration={3000} onClose={() => setCopied(null)}>
        <Alert severity={copied === 'ok' ? 'success' : 'error'} onClose={() => setCopied(null)}>
          {copied === 'ok' ? tUi("Stream link copied. Open it in VLC or any player on this network.") : tUi("Unable to copy the link.")}
        </Alert>
      </Snackbar>
    </>
  );

  if (inline) return open ? <Box component="section" aria-label={tUi("Live TV player")} sx={{ minWidth: 0, bgcolor: 'background.paper', border: 1, borderColor: 'divider', borderRadius: 2 }}>{playerContent}</Box> : null;
  return <Dialog open={open} onClose={handleClose} fullScreen={fullScreen} maxWidth="md" fullWidth aria-labelledby="stream-player-title">{playerContent}</Dialog>;
};

export default StreamPlayerDialog;
