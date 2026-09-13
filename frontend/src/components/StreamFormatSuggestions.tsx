import React from 'react';
import { Alert, Button, Stack, Typography } from '@mui/material';
import { usePublicUrl, useSystemServices } from '../hooks/useSystemServices';

interface StreamFormatSuggestionsProps {
  onSelect: (name: string, pattern: string) => void;
}

/** Prefill editable formats: published sidecar ports can differ from container ports. */
const StreamFormatSuggestions: React.FC<StreamFormatSuggestionsProps> = ({ onSelect }) => {
  const { data: publicUrl } = usePublicUrl();
  const { data, isError } = useSystemServices();
  const formats = [{ name: 'AceStream app', pattern: 'acestream://{channel_id}' }];
  if (publicUrl?.url) {
    formats.push({ name: 'TV channel relay (automatic failover)', pattern: `${publicUrl.url.replace(/\/$/, '')}/tuner/channel/{tv_channel_id}.ts` });
    formats.push({ name: 'Server relay', pattern: `${publicUrl.url.replace(/\/$/, '')}/tuner/stream/{channel_id}.ts` });
    for (const service of data?.services ?? []) {
      if (!service.enabled || !['acestream', 'acexy'].includes(service.name)) continue;
      const url = new URL(publicUrl.url);
      url.protocol = 'http:';
      url.port = service.name === 'acexy' ? '8080' : '6878';
      formats.push({
        name: service.name === 'acexy' ? 'Acexy' : 'AceStream direct',
        pattern: `${url.origin}/ace/getstream?id={channel_id}${service.name === 'acestream' ? '&pid={pid}' : ''}`,
      });
    }
  }
  return <Stack spacing={1}>
    <Typography variant="body2">Start with a suggested format. Review the host and published port before saving.</Typography>
    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
      {formats.map(format => <Button key={format.name} size="small" variant="outlined" onClick={() => onSelect(format.name, format.pattern)}>{format.name}</Button>)}
    </Stack>
    {isError ? <Alert severity="warning">Service suggestions could not be loaded.</Alert> : null}
  </Stack>;
};
export default StreamFormatSuggestions;
