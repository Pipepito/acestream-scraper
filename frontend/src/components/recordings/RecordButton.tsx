import { useQuery } from '@tanstack/react-query';
import { recordingService } from '../../services/recordingService';
import React, { useState } from 'react';
import { Button } from '@mui/material';
import FiberManualRecordRounded from '@mui/icons-material/FiberManualRecordRounded';
import type { EPGProgram } from '../../services/epgService';
const RecordingDialog = React.lazy(() => import('./RecordingDialog'));
interface Props { channelId: number; channelName: string; programme?: EPGProgram }
const RecordButton: React.FC<Props> = (props) => {
  const [open, setOpen] = useState(false);
  const current = useQuery({ queryKey: ['recordings', 'current', props.channelId], queryFn: () => recordingService.currentProgramme(props.channelId), enabled: open && !props.programme, staleTime: 0 });
  return <><Button startIcon={<FiberManualRecordRounded />} onClick={() => setOpen(true)} aria-label={`Record ${props.programme?.title ?? props.channelName}`}>{props.programme && Date.parse(props.programme.start_time) > Date.now() ? 'Schedule recording' : 'Record now'}</Button>
    {open && (props.programme || !current.isLoading) ? <React.Suspense fallback={<span role="status">Opening recording…</span>}><RecordingDialog {...props} programme={props.programme ?? (current.data ? { ...current.data, subtitle: current.data.subtitle ?? undefined, description: current.data.description ?? undefined, category: current.data.category ?? undefined } : undefined)} onClose={() => setOpen(false)} /></React.Suspense> : null}</>;
};
export default RecordButton;
