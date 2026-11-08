import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
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
  const tUi = useUiText();
  const probe = useMutation({ mutationFn: () => searchService.checkBroadcast(channel.id) });
  const catalogueLabel = channel.status === 2
    ? uiText("Catalogue: available")
    : channel.status === 1 ? uiText("Catalogue: uncertain") : uiText("Catalogue: unknown");
  const updatedAt = channel.availability_updated_at;
  const updatedDate = updatedAt ? new Date(updatedAt * 1000) : null;

  return (
    <Box sx={{ minWidth: 180 }}>
      <Typography variant="body2">{catalogueLabel}</Typography>
      {updatedDate && Number.isFinite(updatedDate.getTime()) ? (
        <Typography variant="caption" color="text.secondary" component="div">
          {tUi("Updated")}{' '}{formatRelativeTime(updatedDate.toISOString())}
        </Typography>
      ) : null}
      <Box role="status" aria-label={tUi("Broadcast status for {{value0}}", { value0: channel.name })}>
        {probe.isPending ? (
          <Typography variant="caption">{tUi("Checking broadcast…")}</Typography>
        ) : probe.isError ? (
          <Typography variant="caption" color="error">{tUi("Check failed:")}{' '}{normalizeApiError(probe.error).message}</Typography>
        ) : probe.data ? (
          <>
            <Chip
              size="small"
              color={probe.data.is_online ? 'success' : 'default'}
              label={probe.data.is_online ? tUi("Broadcast detected") : tUi("No broadcast detected")}
              title={probe.data.message}
            />
            <Typography variant="caption" color="text.secondary" component="div">
              {tUi("Checked")}{' '}{formatRelativeTime(probe.data.last_checked)}
            </Typography>
          </>
        ) : <Typography variant="caption" color="text.secondary">{tUi("Broadcast not checked")}</Typography>}
      </Box>
      <Button
        size="small"
        disabled={probe.isPending}
        onClick={() => probe.mutate()}
        aria-label={tUi("Check broadcast for {{value0}}", { value0: channel.name })}
      >
        {probe.data || probe.isError ? tUi("Check again") : tUi("Check broadcast")}
      </Button>
    </Box>
  );
};
export default SearchBroadcastStatus;
