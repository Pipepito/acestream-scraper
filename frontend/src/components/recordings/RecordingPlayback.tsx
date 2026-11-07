import React, { useEffect, useState } from 'react';
import { Alert, LinearProgress, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { recordingFileUrl, recordingService } from '../../services/recordingService';
import { getErrorMessage } from '../../utils/errorUtils';
const RecordingPlayback: React.FC<{ recordingId: string; fileId: string }> = ({ recordingId, fileId }) => {
  const [sessionId, setSessionId] = useState<string>();
  const [error, setError] = useState('');
  const [unsupported, setUnsupported] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let owned: string | undefined;
    void recordingService.openPlayback(recordingId, fileId).then((session) => {
      owned = session.id;
      if (cancelled) void recordingService.closePlayback(recordingId, owned).catch(() => undefined);
      else setSessionId(session.id);
    }).catch((reason: unknown) => { if (!cancelled) setError(getErrorMessage(reason)); });
    return () => { cancelled = true; if (owned) void recordingService.closePlayback(recordingId, owned).catch(() => undefined); };
  }, [recordingId, fileId]);
  const session = useQuery({ queryKey: ['recordings', 'playback', recordingId, sessionId], queryFn: () => recordingService.playback(recordingId, sessionId!), enabled: Boolean(sessionId), refetchInterval: 2000, refetchIntervalInBackground: true });
  if (error || session.isError) return <Alert severity="error">{error || getErrorMessage(session.error)}</Alert>;
  if (unsupported || session.data?.state === 'failed') return <Alert severity="info">This browser cannot play this recording. Download the original. Video is preserved without re-encoding.</Alert>;
  if (session.data?.state !== 'ready') return <><LinearProgress aria-label="Preparing recording playback" /><Typography sx={{ mt: 2 }}>Preparing browser playback. Recording capture takes priority; preparation waits while recording is active.</Typography></>;
  return <video controls preload="metadata" style={{ width: '100%' }} src={recordingFileUrl(recordingId, session.data.file_id)} onError={() => setUnsupported(true)} aria-label="Recording playback"><track kind="captions" /></video>;
};
export default RecordingPlayback;
