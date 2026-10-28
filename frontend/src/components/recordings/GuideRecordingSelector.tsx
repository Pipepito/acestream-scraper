import React, { useState } from 'react';
import { Alert, MenuItem, TextField } from '@mui/material';
import { useTVChannelCatalog } from '../../hooks/useTVChannels';
import ScheduleView from '../epg/ScheduleView';
const GuideRecordingSelector: React.FC<{ epgChannelId: number; sourceId: number; xmlId: string }> = ({ epgChannelId, sourceId, xmlId }) => {
  const channels = useTVChannelCatalog();
  const matches = (channels.data ?? []).filter((item) => item.is_active && item.epg_source_id === sourceId && item.epg_id === xmlId);
  const [selected, setSelected] = useState<number>(0);
  const chosen = matches.length === 1 ? matches[0] : matches.find((item) => item.id === selected);
  return <>
    {matches.length > 1 ? <TextField select fullWidth label="TV Channel to record" value={selected || ''} onChange={(e) => setSelected(Number(e.target.value))} sx={{ mb: 2 }}>{matches.map((item) => <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>)}</TextField> : null}
    {!channels.isLoading && !matches.length ? <Alert severity="info">Assign this guide to a TV Channel to schedule recordings.</Alert> : null}
    <ScheduleView epgChannelId={epgChannelId} tvChannelId={chosen?.id} tvChannelName={chosen?.name} />
  </>;
};
export default GuideRecordingSelector;
