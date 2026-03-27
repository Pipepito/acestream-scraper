import React, { useState } from 'react';
import { useEPGPrograms, useResolveEPGChannel } from '../hooks/useEPG';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Typography, Box, TextField, LinearProgress, Chip } from '@mui/material';
import ContentSection from './layout/ContentSection';
import { getLocalISODate, getRelativeLocalISODate } from '../utils/dateUtils';

interface EPGProgramsTableProps {
  epgId: string;
  epgSourceId?: number;
}

const EPGProgramsTable: React.FC<EPGProgramsTableProps> = ({ epgId, epgSourceId }) => {
  const [dateRange, setDateRange] = useState({
    start: getLocalISODate(),
    end: getRelativeLocalISODate(7)
  });
  const { data: epgChannel, isLoading: loadingChannels } = useResolveEPGChannel(epgSourceId, epgId);
  const epgChannelId = epgChannel?.id;
  const { data: programs, isLoading } = useEPGPrograms(
    epgChannelId ?? 0,
    dateRange.start,
    dateRange.end
  );

  if (loadingChannels) return <LinearProgress sx={{ mb: 2 }} />;
  if (!epgChannelId) return <Typography variant="body2">No EPG channel found for this TV channel.</Typography>;

  return (
    <ContentSection
      title="Program Schedule"
      description="Use the date controls to review the resolved EPG timeline for this channel."
    >
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        <Chip label={epgChannel.name} size="small" color="info" />
        <Chip label={`${programs?.length || 0} program${programs?.length === 1 ? '' : 's'} loaded`} size="small" />
      </Box>
      <Box display="flex" gap={2} mb={2} flexWrap="wrap">
        <TextField
          label="Start Date"
          type="date"
          value={dateRange.start}
          onChange={e => setDateRange(d => ({ ...d, start: e.target.value }))}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          label="End Date"
          type="date"
          value={dateRange.end}
          onChange={e => setDateRange(d => ({ ...d, end: e.target.value }))}
          InputLabelProps={{ shrink: true }}
        />
      </Box>
      {isLoading ? <LinearProgress sx={{ mb: 2 }} /> : null}
      <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Start</TableCell>
              <TableCell>End</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Subtitle</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {programs?.length ? programs.map(program => (
              <TableRow key={program.id}>
                <TableCell>{program.start_time}</TableCell>
                <TableCell>{program.end_time}</TableCell>
                <TableCell>{program.title}</TableCell>
                <TableCell>{program.subtitle}</TableCell>
                <TableCell>{program.category}</TableCell>
                <TableCell>{program.description?.slice(0, 100)}</TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body2">No EPG programs found for this channel.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </ContentSection>
  );
};

export default EPGProgramsTable;
