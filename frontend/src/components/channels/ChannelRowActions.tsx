import React from 'react';
import { Box, CircularProgress, IconButton, Tooltip } from '@mui/material';
import { Delete, Edit, Refresh, Star, StarBorder, VisibilityOff, Visibility } from '@mui/icons-material';
import TvIcon from '@mui/icons-material/Tv';
import LinkIcon from '@mui/icons-material/Link';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
import RowActionsMenu from '../RowActionsMenu';
import type { AcestreamChannel } from '../../services/channelService';

export interface ChannelActionHandlers {
  onPlay: (channel: AcestreamChannel) => void;
  onCheckStatus: (channel: AcestreamChannel) => void;
  onEdit: (channel: AcestreamChannel) => void;
  onToggleHidden: (channel: AcestreamChannel) => void;
  onAssignTV: (channel: AcestreamChannel) => void;
  onOpenTV: (channel: AcestreamChannel) => void;
  onToggleTVFavorite: (channel: AcestreamChannel) => void;
  onDelete: (channel: AcestreamChannel) => void;
}

export interface ChannelRowActionsProps extends ChannelActionHandlers {
  channel: AcestreamChannel;
  checking?: boolean;
}

/** Two visible actions (play, check status) plus a "More actions" menu; shared by the table and the phone cards. */
const ChannelRowActions: React.FC<ChannelRowActionsProps> = ({
  channel,
  checking = false,
  onPlay,
  onCheckStatus,
  onEdit,
  onToggleHidden,
  onAssignTV,
  onOpenTV,
  onToggleTVFavorite,
  onDelete,
}) => {
  const linkedName = channel.tv_channel_name || 'linked TV channel';
  const hidden = channel.is_active === false;

  const menuActions = [
    channel.tv_channel_id
      ? { label: `Open TV channel: ${linkedName}`, icon: <TvIcon fontSize="small" />, onClick: () => onOpenTV(channel) }
      : { label: 'Link to a TV channel', icon: <LinkIcon fontSize="small" />, onClick: () => onAssignTV(channel) },
    { label: 'Edit', icon: <Edit fontSize="small" />, onClick: () => onEdit(channel) },
    {
      label: hidden ? 'Show in playlist' : 'Hide from playlist',
      icon: hidden ? <Visibility fontSize="small" /> : <VisibilityOff fontSize="small" />,
      onClick: () => onToggleHidden(channel),
    },
    ...(channel.tv_channel_id
      ? [
          {
            label: channel.tv_channel_is_favorite ? `Remove ${linkedName} from favorites` : `Add ${linkedName} to favorites`,
            icon: channel.tv_channel_is_favorite ? <Star fontSize="small" /> : <StarBorder fontSize="small" />,
            onClick: () => onToggleTVFavorite(channel),
          },
        ]
      : []),
    { label: 'Delete', icon: <Delete fontSize="small" />, danger: true, onClick: () => onDelete(channel) },
  ];

  return (
    <Box role="group" aria-label={`Acestream channel actions for ${channel.name}`} sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
      <Tooltip title="Play in the browser">
        <IconButton
          size="small"
          color="primary"
          aria-label={`play channel ${channel.name}`}
          onClick={(event) => {
            event.stopPropagation();
            onPlay(channel);
          }}
        >
          <PlayArrowRounded fontSize="small" />
        </IconButton>
      </Tooltip>
      <Tooltip title="Check status">
        <span>
          <IconButton
            size="small"
            aria-label={`check channel status ${channel.name}`}
            disabled={checking}
            onClick={(event) => {
              event.stopPropagation();
              onCheckStatus(channel);
            }}
          >
            {checking ? <CircularProgress size={16} /> : <Refresh fontSize="small" />}
          </IconButton>
        </span>
      </Tooltip>
      <RowActionsMenu label={`More actions for ${channel.name}`} actions={menuActions} />
    </Box>
  );
};

export default ChannelRowActions;
