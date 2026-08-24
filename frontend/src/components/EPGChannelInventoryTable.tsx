import React from 'react';
import {
  Box,
  Checkbox,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { Visibility as VisibilityIcon } from '@mui/icons-material';
import { EPGChannel, EPGSource } from '../services/epgService';

interface EPGChannelInventoryTableProps {
  channels: EPGChannel[];
  sources: EPGSource[] | undefined;
  selectedChannelIds: number[];
  visibleUnmappedChannelIds: number[];
  isTVChannelCatalogReady: boolean;
  isChannelMapped: (channel: EPGChannel) => boolean;
  onSelectAll: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onSelectChannel: (id: number) => void;
  onViewPrograms: (id: number) => void;
}

const EPGChannelInventoryTable: React.FC<EPGChannelInventoryTableProps> = ({
  channels,
  sources,
  selectedChannelIds,
  visibleUnmappedChannelIds,
  isTVChannelCatalogReady,
  isChannelMapped,
  onSelectAll,
  onSelectChannel,
  onViewPrograms,
}) => (
  <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
    <Table>
      <TableHead>
        <TableRow>
          <TableCell padding="checkbox">
            <Checkbox
              indeterminate={selectedChannelIds.length > 0 && selectedChannelIds.length < visibleUnmappedChannelIds.length}
              checked={visibleUnmappedChannelIds.length > 0 && selectedChannelIds.length === visibleUnmappedChannelIds.length}
              disabled={!isTVChannelCatalogReady}
              onChange={onSelectAll}
              inputProps={{ 'aria-label': 'select all EPG channels' }}
            />
          </TableCell>
          <TableCell>Name</TableCell>
          <TableCell>XML ID</TableCell>
          <TableCell>Source</TableCell>
          <TableCell>Language</TableCell>
          <TableCell>Actions</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {(channels || []).map((channel) => (
          <TableRow key={channel.id} selected={selectedChannelIds.includes(channel.id)}>
            <TableCell padding="checkbox">
              <Checkbox
                checked={selectedChannelIds.includes(channel.id)}
                onChange={() => onSelectChannel(channel.id)}
                inputProps={{ 'aria-label': `select EPG channel ${channel.name}` }}
                disabled={!isTVChannelCatalogReady || isChannelMapped(channel)}
              />
            </TableCell>
            <TableCell>
              {channel.name}
              {channel.icon_url && (
                <Box
                  component="img"
                  src={channel.icon_url}
                  alt={channel.name}
                  sx={{ height: 30, marginLeft: 1.25, verticalAlign: 'middle' }}
                />
              )}
            </TableCell>
            <TableCell>{channel.channel_xml_id}</TableCell>
            <TableCell>
              {sources?.find(s => s.id === channel.epg_source_id)?.name || channel.epg_source_id}
            </TableCell>
            <TableCell>{channel.language || 'Unknown'}</TableCell>
            <TableCell>
            <IconButton
              color="primary"
              title="View Programs"
              aria-label={`View programs for ${channel.name}`}
              onClick={() => onViewPrograms(channel.id)}
            >
              <VisibilityIcon />
            </IconButton>
            </TableCell>
          </TableRow>
        ))}
        {channels && channels.length === 0 && (
          <TableRow>
            <TableCell colSpan={6} align="center">
              No EPG channels found
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  </TableContainer>
);

export default EPGChannelInventoryTable;
