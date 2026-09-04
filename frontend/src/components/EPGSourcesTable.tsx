import React from 'react';
import {
  Box,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { EPGSource } from '../services/epgService';

interface EPGSourcesTableProps {
  sources: EPGSource[] | undefined;
  refreshingSourceId: number | null;
  onRefreshSource: (id: number) => void;
  onEditSource: (source: EPGSource) => void;
  onDeleteSource: (id: number) => void;
}

const EPGSourcesTable: React.FC<EPGSourcesTableProps> = ({
  sources,
  refreshingSourceId,
  onRefreshSource,
  onEditSource,
  onDeleteSource,
}) => (
  <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>Name</TableCell>
          <TableCell>URL</TableCell>
          <TableCell>Status</TableCell>
          <TableCell>Last Updated</TableCell>
          <TableCell>Actions</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {(sources || []).map((source) => (
          <TableRow key={source.id}>
            <TableCell>{source.name}</TableCell>
            <TableCell>{source.url}</TableCell>
            <TableCell>
              {source.enabled ? (
                <Chip label="Enabled" color="success" size="small" />
              ) : (
                <Chip label="Disabled" color="default" size="small" />
              )}
              {source.error_count > 0 ? (
                <Typography variant="caption" color="error.main" component="p" sx={{ mt: 0.5, maxWidth: 360, overflowWrap: 'anywhere' }}>
                  {source.error_count} failed refresh{source.error_count === 1 ? '' : 'es'}
                  {source.last_error ? ` · ${source.last_error}` : ''}
                </Typography>
              ) : null}
            </TableCell>
            <TableCell>
              {source.last_updated ? (
                formatDistanceToNow(new Date(source.last_updated), { addSuffix: true })
              ) : (
                'Never'
              )}
            </TableCell>
            <TableCell>
              <IconButton
                color="primary"
                onClick={() => onRefreshSource(source.id)}
                disabled={refreshingSourceId === source.id}
                aria-label={`Refresh source ${source.name}`}
              >
                <RefreshIcon />
              </IconButton>
              <IconButton color="secondary" onClick={() => onEditSource(source)} aria-label={`Edit source ${source.name}`}>
                <EditIcon />
              </IconButton>
              <IconButton color="error" onClick={() => onDeleteSource(source.id)} aria-label={`Delete source ${source.name}`}>
                <DeleteIcon />
              </IconButton>
            </TableCell>
          </TableRow>
        ))}
        {sources && sources.length === 0 && (
          <TableRow>
            <TableCell colSpan={5} align="center">
              No EPG sources found
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  </TableContainer>
);

export default EPGSourcesTable;
