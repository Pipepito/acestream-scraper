import React from 'react';
import { Box, Button, Checkbox, Chip, IconButton, Paper, Stack, Tooltip, Typography, useTheme } from '@mui/material';
import { ContentCopy } from '@mui/icons-material';
import EmptyState from '../state/EmptyState';
import ChannelRowActions, { type ChannelActionHandlers } from './ChannelRowActions';
import OnlineChip from './OnlineChip';
import type { AcestreamChannel } from '../../services/channelService';
import { formatRelativeTime } from '../../utils/format';
import { formatDateTime } from '../../utils/formatters';

export interface ChannelCardListProps extends ChannelActionHandlers {
  channels: AcestreamChannel[];
  loading: boolean;
  checkingStatus: Record<string, boolean>;
  selectedIds: string[];
  onSelectionChange: (ids: string[]) => void;
  totalCount: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onCopyId: (id: string) => void;
}

/** Phone-width replacement for the channel grid: one card per channel with the same actions. */
const ChannelCardList: React.FC<ChannelCardListProps> = ({
  channels,
  loading,
  checkingStatus,
  selectedIds,
  onSelectionChange,
  totalCount,
  page,
  pageSize,
  onPageChange,
  onCopyId,
  ...handlers
}) => {
  const theme = useTheme();
  const rangeStart = totalCount === 0 ? 0 : page * pageSize + 1;
  const rangeEnd = Math.min(totalCount, (page + 1) * pageSize);
  const lastPage = totalCount === 0 ? 0 : Math.ceil(totalCount / pageSize) - 1;

  const toggleSelected = (id: string, checked: boolean) => {
    onSelectionChange(checked ? [...selectedIds, id] : selectedIds.filter((selected) => selected !== id));
  };

  if (!loading && channels.length === 0) {
    return (
      <EmptyState
        title={totalCount === 0 ? 'No channels to show' : 'No channels on this page'}
        description={totalCount === 0 ? 'Adjust your filters or add a channel.' : 'Move to another page to keep browsing.'}
      />
    );
  }

  return (
    <Stack spacing={1.5} aria-busy={loading}>
      {channels.map((channel) => {
        const hidden = channel.is_active === false;
        return (
          <Paper
            key={channel.id}
            component="article"
            aria-label={channel.name}
            variant="outlined"
            sx={{ p: 1.5, borderRadius: 2, borderColor: theme.appTokens.surface.border, backgroundColor: theme.appTokens.surface.raised }}
          >
            <Stack direction="row" spacing={1} alignItems="flex-start">
              <Checkbox
                size="small"
                checked={selectedIds.includes(channel.id)}
                onChange={(event) => toggleSelected(channel.id, event.target.checked)}
                inputProps={{ 'aria-label': `Select ${channel.name}` }}
                sx={{ mt: -0.5, ml: -1 }}
              />
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography component="h3" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
                  {channel.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {channel.group || 'No group'}
                  {channel.tv_channel_name ? ` · TV: ${channel.tv_channel_name}` : ''}
                </Typography>
              </Box>
            </Stack>

            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
              <OnlineChip isOnline={channel.is_online} />
              {hidden ? <Chip label="Hidden" size="small" variant="outlined" sx={{ minWidth: 72 }} /> : null}
              <Tooltip title={channel.last_checked ? formatDateTime(channel.last_checked) : 'Never checked'}>
                <Typography variant="body2" color="text.secondary">
                  Checked {formatRelativeTime(channel.last_checked)}
                </Typography>
              </Tooltip>
            </Stack>

            <Stack direction="row" alignItems="center" sx={{ mt: 1, fontFamily: 'monospace', fontSize: 12.5, minWidth: 0 }}>
              <Box component="span" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {channel.id}
              </Box>
              <Tooltip title="Copy ID">
                <IconButton size="small" aria-label={`copy acestream id ${channel.id}`} onClick={() => onCopyId(channel.id)}>
                  <ContentCopy fontSize="inherit" />
                </IconButton>
              </Tooltip>
            </Stack>

            <Box sx={{ mt: 1 }}>
              <ChannelRowActions channel={channel} checking={Boolean(checkingStatus[channel.id])} {...handlers} />
            </Box>
          </Paper>
        );
      })}

      {totalCount > 0 ? (
        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between" sx={{ pt: 0.5 }}>
          <Typography variant="body2" color="text.secondary">
            {rangeStart}–{rangeEnd} of {totalCount}
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button size="small" variant="outlined" disabled={page === 0} onClick={() => onPageChange(page - 1)} aria-label="Go to previous page">
              Previous
            </Button>
            <Button size="small" variant="outlined" disabled={page >= lastPage} onClick={() => onPageChange(page + 1)} aria-label="Go to next page">
              Next
            </Button>
          </Stack>
        </Stack>
      ) : null}
    </Stack>
  );
};

export default ChannelCardList;
