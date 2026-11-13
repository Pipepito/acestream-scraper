import { useUiText } from '../../i18n/useUiText';
import { useQuery } from '@tanstack/react-query';
import { recordingService } from '../../services/recordingService';
import React, { useState } from 'react';
import { Button, Typography } from '@mui/material';
import FiberManualRecordRounded from '@mui/icons-material/FiberManualRecordRounded';
import type { EPGProgram } from '../../services/epgService';
const RecordingDialog = React.lazy(() => import('./RecordingDialog'));
interface Props { channelId: number; channelName: string; programme?: EPGProgram; disabled?: boolean }
const RecordButton: React.FC<Props> = (props) => {
  const tUi = useUiText();
  const [open, setOpen] = useState(false);
  const [saved, setSaved] = useState(false);
  const current = useQuery({ queryKey: ['recordings', 'current', props.channelId], queryFn: () => recordingService.currentProgramme(props.channelId), enabled: open && !props.programme, staleTime: 0 });
  return <><Button disabled={props.disabled} startIcon={<FiberManualRecordRounded />} onClick={() => { setSaved(false); setOpen(true); }} aria-label={tUi("Record {{value0}}", { value0: props.programme?.title ?? props.channelName })}>{props.programme && Date.parse(props.programme.start_time) > Date.now() ? tUi("Schedule recording") : tUi("Record now")}</Button>
    {open && (props.programme || !current.isLoading) ? <React.Suspense fallback={<span role="status">{tUi("Opening recording…")}</span>}><RecordingDialog {...props} programme={props.programme ?? (current.data ? { ...current.data, subtitle: current.data.subtitle ?? undefined, description: current.data.description ?? undefined, category: current.data.category ?? undefined } : undefined)} onSaved={() => setSaved(true)} onClose={() => setOpen(false)} /></React.Suspense> : null}{saved ? <Typography role="status" variant="body2">{tUi("Recording saved. View it in Recordings.")}</Typography> : null}</>;
};
export default RecordButton;
