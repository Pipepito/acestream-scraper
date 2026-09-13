import React from 'react';
import { Box, Checkbox, Chip, Link, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
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
}

/** Guide channels of the chosen source. Source and Language columns only appear when they carry information. */
const EPGChannelInventoryTable: React.FC<EPGChannelInventoryTableProps> = ({
  channels,
  sources,
  selectedChannelIds,
  visibleUnmappedChannelIds,
  isTVChannelCatalogReady,
  isChannelMapped,
  onSelectAll,
  onSelectChannel,
}) => {
  const showSource = (sources?.length ?? 0) > 1;
  const showLanguage = channels.some((channel) => Boolean(channel.language));
  const columnCount = 4 + (showSource ? 1 : 0) + (showLanguage ? 1 : 0);

  return (
    <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
      <Table size="small" aria-label="Guide channels">
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
            {showSource ? <TableCell>Source</TableCell> : null}
            {showLanguage ? <TableCell>Language</TableCell> : null}
            <TableCell>TV channel</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {(channels || []).map((channel) => {
            const mapped = isChannelMapped(channel);
            return (
              <TableRow key={channel.id} selected={selectedChannelIds.includes(channel.id)}>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedChannelIds.includes(channel.id)}
                    onChange={() => onSelectChannel(channel.id)}
                    inputProps={{ 'aria-label': `select EPG channel ${channel.name}` }}
                    disabled={!isTVChannelCatalogReady || mapped}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {channel.icon_url ? <Box component="img" src={channel.icon_url} alt="" sx={{ height: 24, width: 24, objectFit: 'contain' }} /> : null}
                    <Link component={RouterLink} to={`/epg/channels/${channel.id}`} sx={{ fontWeight: 600 }}>
                      {channel.name}
                    </Link>
                  </Box>
                </TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontSize: 12.5 }}>{channel.channel_xml_id}</TableCell>
                {showSource ? <TableCell>{sources?.find((s) => s.id === channel.epg_source_id)?.name || channel.epg_source_id}</TableCell> : null}
                {showLanguage ? <TableCell>{channel.language || '—'}</TableCell> : null}
                <TableCell>
                  {mapped ? <Chip label="Linked" size="small" color="success" variant="outlined" /> : <Chip label="Not linked" size="small" variant="outlined" />}
                </TableCell>
              </TableRow>
            );
          })}
          {channels && channels.length === 0 && (
            <TableRow>
              <TableCell colSpan={columnCount} align="center">
                No EPG channels found
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default EPGChannelInventoryTable;
