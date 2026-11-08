import { getLocale } from '../../i18n/locale';
import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Alert, Box, Button, Chip, Divider, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { systemService } from '../../services/systemService';
import ContentSection from '../layout/ContentSection';
import { formatRelativeTime } from '../../utils/format';

const bytes = (value: number | null | undefined) => {
  if (value == null) return 'Unavailable';
  const index = value > 0 ? Math.min(Math.floor(Math.log(value) / Math.log(1024)), 4) : 0;
  return `${(value / 1024 ** index).toLocaleString(getLocale(), { maximumFractionDigits: 1 })} ${['B', 'KiB', 'MiB', 'GiB', 'TiB'][index]}`;
};

export default function StoragePanel() {
  const tUi = useUiText();
  const query = useQuery({ queryKey: ['system-storage'], queryFn: systemService.getStorage, staleTime: 60_000, refetchInterval: 60_000 });
  return <ContentSection title={tUi("Storage")} description={tUi("Container directories and the free space available on their filesystems.")} actions={<Button disabled={query.isFetching} onClick={() => void query.refetch()}>{tUi("Refresh storage")}</Button>}>
    {query.isLoading ? <Typography role="status">{tUi("Checking storage…")}</Typography> : query.isError ? <Alert severity="warning">{tUi("Could not read storage information. Try refreshing.")}</Alert> : query.data ? <Stack spacing={2}>
      {(query.data.configuration_warnings ?? []).map(warning => <Alert severity="warning" key={warning.legacy}>
        {warning.legacy} {' '}{tUi("is deprecated. Rename it to")}{' '}{warning.replacement}. {warning.selected === warning.legacy ? tUi("The old name still works.") : tUi("The new name takes precedence when both are set.")}
      </Alert>)}
      {query.data.message && <Alert severity="info">{query.data.message}</Alert>}
      {query.data.mount_detection === 'unavailable' && <Alert severity="info">{tUi("Mount information is unavailable on this system. Showing configured directories where possible.")}</Alert>}
      <Stack divider={<Divider />} spacing={1.5}>
        {query.data.directories.map(directory => <Box key={directory.path} sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(180px, 1fr) 2fr' }, gap: 1.5 }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography component="h3" variant="body2" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>{directory.path}</Typography>
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mt: 0.5 }}>
              <Chip size="small" variant="outlined" label={directory.mounted == null ? tUi("Mount unknown") : directory.mounted ? tUi("Mounted storage") : tUi("Container filesystem")} />
              {directory.read_only && <Chip size="small" label={tUi("Read only")} />}
            </Stack>
            {directory.mount_point && directory.mount_point !== directory.path && <Typography variant="caption" color="text.secondary">{tUi("On")}{' '}{directory.mount_point}</Typography>}
          </Box>
          <Box>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 1 }}>
              {[
                ['Directory size', tUi("{{value0}}{{value1}}", { value0: directory.directory_bytes != null && !directory.size_complete ? 'At least ' : '', value1: bytes(directory.directory_bytes) })],
                ['Free space', bytes(directory.filesystem_free_bytes)],
                ['Filesystem total', bytes(directory.filesystem_total_bytes)],
              ].map(([label, value]) => <Box key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}>{value}</Typography></Box>)}
            </Box>
            {directory.message && <Typography variant="caption" color="text.secondary">{directory.message}</Typography>}
          </Box>
        </Box>)}
      </Stack>
      <Typography variant="caption" color="text.secondary">{tUi("Checked")}{' '}{formatRelativeTime(query.data.checked_at)}{tUi("; scans are cached for one minute. Free space is shared by directories on the same filesystem, not reserved for each directory. Sizes count allocated file space and exclude symbolic links and nested mounts. Host folder paths and Docker volume names are not available from inside the container.")}</Typography>
    </Stack> : null}
  </ContentSection>;
}
