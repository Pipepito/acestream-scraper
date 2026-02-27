import React, { useState } from 'react';
import { useEPGPrograms, useEPGChannels } from '../hooks/useEPG';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Box, TextField, LinearProgress } from '@mui/material';

interface EPGProgramsTableProps {
  epgId: string;
}

const EPGProgramsTable: React.FC<EPGProgramsTableProps> = ({ epgId }) => {
  const [dateRange, setDateRange] = useState({
    start: new Date().toISOString().split('T')[0],
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });
  // Lookup EPG channel by XML ID
  const { data: epgChannels, isLoading: loadingChannels } = useEPGChannels();
  const epgChannel = epgChannels?.find(c => c.channel_xml_id === epgId);
  const epgChannelId = epgChannel?.id;
  const { data: programs, isLoading } = useEPGPrograms(
    epgChannelId ?? 0,
    dateRange.start,
    dateRange.end
  );

  if (loadingChannels) return <LinearProgress sx={{ mb: 2 }} />;
  if (!epgChannelId) return <Typography variant="body2">No EPG channel found for this TV channel.</Typography>;

  return (
    <Box>
      <Box display="flex" gap={2} mb={2}>
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
      <TableContainer component={Paper}>
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
    </Box>
  );
};

export default EPGProgramsTable;
