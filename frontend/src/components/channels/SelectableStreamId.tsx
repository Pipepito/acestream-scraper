import React, { useRef } from 'react';
import { Box, IconButton, InputBase, Tooltip } from '@mui/material';
import { ContentCopy } from '@mui/icons-material';
import NetworkStatusChip from './NetworkStatusChip';

interface Props {
  id: string;
  networkStatus?: string | null;
  onCopyId: (id: string) => void;
}

/** Select first: manual copying remains available when HTTP blocks clipboard access. */
export default function SelectableStreamId({ id, networkStatus, onCopyId }: Props) {
  const input = useRef<HTMLInputElement>(null);
  return (
    <Box sx={{ width: '100%', minWidth: 0 }} onClick={(event) => event.stopPropagation()}>
      <InputBase
        value={id}
        inputRef={input}
        readOnly
        fullWidth
        inputProps={{ 'aria-label': `Acestream ID ${id}`, spellCheck: false }}
        onFocus={(event) => event.target.select()}
        onClick={() => input.current?.select()}
        sx={{ fontFamily: 'monospace', fontSize: 12, '& input': { py: 0.5, userSelect: 'text' }, '&:focus-within': { outline: '2px solid', outlineColor: 'primary.main', borderRadius: 0.5 } }}
      />
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Tooltip title="Copy ID · select the field to copy manually">
          <IconButton size="small" aria-label={`copy acestream id ${id}`} onClick={() => {
            input.current?.focus();
            input.current?.select();
            onCopyId(id);
          }}>
            <ContentCopy fontSize="inherit" />
          </IconButton>
        </Tooltip>
        <NetworkStatusChip status={networkStatus} />
      </Box>
    </Box>
  );
}
