import React from 'react';
import { Box, Button, Chip, Typography } from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { SearchResultItem, searchService } from '../services/searchService';
import { normalizeApiError } from '../services/apiErrors';
import { formatRelativeTime } from '../utils/format';

interface Props {
  channel: SearchResultItem;
}

const SearchBroadcastStatus: React.FC<Props> = ({ channel }) => {
  const probe = useMutation({ mutationFn: () => searchService.checkBroadcast(channel.id) });
  const catalogueLabel = channel.status === 2
    ? 'Catalogue: available'
    : channel.status === 1 ? 'Catalogue: uncertain' : 'Catalogue: unknown';
  const updatedAt = channel.availability_updated_at;
  const updatedDate = updatedAt ? new Date(updatedAt * 1000) : null;

  return (
    <Box sx={{ minWidth: 180 }}>
      <Typography variant="body2">{catalogueLabel}</Typography>
      {updatedDate && Number.isFinite(updatedDate.getTime()) ? (
        <Typography variant="caption" color="text.secondary" component="div">
          Updated {formatRelativeTime(updatedDate.toISOString())}
        </Typography>
      ) : null}
      <Box role="status" aria-label={`Broadcast status for ${channel.name}`}>
        {probe.isPending ? (
          <Typography variant="caption">Checking broadcast…</Typography>
        ) : probe.isError ? (
          <Typography variant="caption" color="error">Check failed: {normalizeApiError(probe.error).message}</Typography>
        ) : probe.data ? (
          <>
            <Chip
              size="small"
              color={probe.data.is_online ? 'success' : 'default'}
              label={probe.data.is_online ? 'Broadcast detected' : 'No broadcast detected'}
              title={probe.data.message}
            />
            <Typography variant="caption" color="text.secondary" component="div">
              Checked {formatRelativeTime(probe.data.last_checked)}
            </Typography>
          </>
        ) : <Typography variant="caption" color="text.secondary">Broadcast not checked</Typography>}
      </Box>
      <Button
        size="small"
        disabled={probe.isPending}
        onClick={() => probe.mutate()}
        aria-label={`Check broadcast for ${channel.name}`}
      >
        {probe.data || probe.isError ? 'Check again' : 'Check broadcast'}
      </Button>
    </Box>
  );
};
export default SearchBroadcastStatus;
