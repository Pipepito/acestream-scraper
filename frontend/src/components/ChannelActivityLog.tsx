import React, { useEffect, useState } from 'react';
import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress, Alert } from '@mui/material';
import { acestreamChannelService } from '../services/channelService';

interface ActivityLogEntry {
  id: number;
  timestamp: string;
  type: string;
  message: string;
  details?: string;
  user?: string;
}

interface ChannelActivityLogProps {
  channelId: string;
}

const ChannelActivityLog: React.FC<ChannelActivityLogProps> = ({ channelId }) => {
  const [log, setLog] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    acestreamChannelService.getAcestreamChannelActivityLog(channelId, { days: 30, page: 1, page_size: 50 })
      .then((data) => {
        setLog(data.items || []);
        setLoading(false);
      })
      .catch((err) => {
        setError('Failed to load activity log');
        setLoading(false);
      });
  }, [channelId]);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Box mt={2}>
      <Typography variant="h6" gutterBottom>Activity Log</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>User</TableCell>
              <TableCell>Details</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {log.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">No activity found</TableCell>
              </TableRow>
            ) : (
              log.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>{new Date(entry.timestamp).toLocaleString()}</TableCell>
                  <TableCell>{entry.type}</TableCell>
                  <TableCell>{entry.message}</TableCell>
                  <TableCell>{entry.user || '-'}</TableCell>
                  <TableCell>{entry.details || '-'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default ChannelActivityLog;
