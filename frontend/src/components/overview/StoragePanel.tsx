import React from 'react';
import { Alert, Box, Button, Chip, Divider, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '../../services/systemService';
import ContentSection from '../layout/ContentSection';
import { formatRelativeTime } from '../../utils/format';

const bytes = (value: number | null | undefined) => {
  if (value == null) return 'Unavailable';
  const index = value > 0 ? Math.min(Math.floor(Math.log(value) / Math.log(1024)), 4) : 0;
  return `${(value / 1024 ** index).toLocaleString(undefined, { maximumFractionDigits: 1 })} ${['B', 'KiB', 'MiB', 'GiB', 'TiB'][index]}`;
};

export default function StoragePanel() {
  const query = useQuery({ queryKey: ['system-storage'], queryFn: systemService.getStorage, staleTime: 60_000, refetchInterval: 60_000 });
  return <ContentSection title="Storage" description="Container directories and the free space available on their filesystems." actions={<Button disabled={query.isFetching} onClick={() => void query.refetch()}>Refresh storage</Button>}>
    {query.isLoading ? <Typography role="status">Checking storage…</Typography> : query.isError ? <Alert severity="warning">Could not read storage information. Try refreshing.</Alert> : query.data ? <Stack spacing={2}>
      {(query.data.configuration_warnings ?? []).map(warning => <Alert severity="warning" key={warning.legacy}>
        {warning.legacy} is deprecated. Rename it to {warning.replacement}. {warning.selected === warning.legacy ? 'The old name still works.' : 'The new name takes precedence when both are set.'}
      </Alert>)}
      {query.data.message && <Alert severity="info">{query.data.message}</Alert>}
      {query.data.mount_detection === 'unavailable' && <Alert severity="info">Mount information is unavailable on this system. Showing configured directories where possible.</Alert>}
      <Stack divider={<Divider />} spacing={1.5}>
        {query.data.directories.map(directory => <Box key={directory.path} sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(180px, 1fr) 2fr' }, gap: 1.5 }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography component="h3" variant="body2" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>{directory.path}</Typography>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mt: 0.5 }}>
              <Chip size="small" variant="outlined" label={directory.mounted == null ? 'Mount unknown' : directory.mounted ? 'Mounted storage' : 'Container filesystem'} />
              {directory.read_only && <Chip size="small" label="Read only" />}
            </Stack>
            {directory.mount_point && directory.mount_point !== directory.path && <Typography variant="caption" color="text.secondary">On {directory.mount_point}</Typography>}
          </Box>
          <Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 1 }}>
              {[
                ['Directory size', `${directory.directory_bytes != null && !directory.size_complete ? 'At least ' : ''}${bytes(directory.directory_bytes)}`],
                ['Free space', bytes(directory.filesystem_free_bytes)],
                ['Filesystem total', bytes(directory.filesystem_total_bytes)],
              ].map(([label, value]) => <Box key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{value}</Typography></Box>)}
            </Box>
            {directory.message && <Typography variant="caption" color="text.secondary">{directory.message}</Typography>}
          </Box>
        </Box>)}
      </Stack>
      <Typography variant="caption" color="text.secondary">Checked {formatRelativeTime(query.data.checked_at)}; scans are cached for one minute. Free space is shared by directories on the same filesystem, not reserved for each directory. Sizes count allocated file space and exclude symbolic links and nested mounts. Host folder paths and Docker volume names are not available from inside the container.</Typography>
    </Stack> : null}
  </ContentSection>;
}
