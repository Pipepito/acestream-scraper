import React from 'react';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { EPGMatchAnalysisResponse, EPGMatchAnalysisRow } from '../services/tvChannelService';
import { MatchFilter } from '../hooks/useEPGMatchAnalysis';

interface EPGMatchAnalysisPanelProps {
  analysis: EPGMatchAnalysisResponse;
  matchFilter: MatchFilter;
  onMatchFilterChange: (filter: MatchFilter) => void;
  filteredRows: EPGMatchAnalysisRow[];
  selectedRowIds: number[];
  onToggleRow: (row: EPGMatchAnalysisRow) => void;
}

const formatMatchLabel = (value?: string | null) => {
  if (!value) return 'Unmatched';

  const specialCases: Record<string, string> = {
    xml_id_exact: 'XML ID exact',
    name_exact: 'Name exact',
    name_similarity: 'Name similarity',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  };

  if (specialCases[value]) {
    return specialCases[value];
  }

  return value
    .split('_')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(' ');
};

const EPGMatchAnalysisPanel: React.FC<EPGMatchAnalysisPanelProps> = ({
  analysis,
  matchFilter,
  onMatchFilterChange,
  filteredRows,
  selectedRowIds,
  onToggleRow,
}) => (
  <Box sx={{ p: 2, mb: 0, border: 1, borderColor: 'divider', borderRadius: 2 }}>
    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
      <Typography variant="body2">{analysis.summary.epg_channels_analyzed} analyzed</Typography>
      <Typography variant="body2">{analysis.summary.matched_epg_channels} matched</Typography>
      <Typography variant="body2">{analysis.summary.creatable_rows} creatable</Typography>
    </Box>

    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
      <Button variant={matchFilter === 'all' ? 'contained' : 'outlined'} size="small" onClick={() => onMatchFilterChange('all')}>
        All
      </Button>
      <Button variant={matchFilter === 'matched' ? 'contained' : 'outlined'} size="small" onClick={() => onMatchFilterChange('matched')}>
        Matched
      </Button>
      <Button variant={matchFilter === 'unmatched' ? 'contained' : 'outlined'} size="small" onClick={() => onMatchFilterChange('unmatched')}>
        Unmatched
      </Button>
      <Button variant={matchFilter === 'creatable' ? 'contained' : 'outlined'} size="small" onClick={() => onMatchFilterChange('creatable')}>
        Creatable
      </Button>
    </Box>

    {analysis.rows.length === 0 || analysis.summary.matched_epg_channels === 0 ? (
      <Alert severity="info">No matches met the current strictness.</Alert>
    ) : (
      <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">Select</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Match Type</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRows.map((row) => {
              const isSelected = selectedRowIds.includes(row.epg_channel_id);
              const isDisabled = !row.is_creatable;
              const statusLabel = row.existing_tv_channel_id
                ? 'Already exists'
                : row.candidate_count === 0
                  ? 'No candidate'
                  : row.is_creatable
                    ? 'Creatable'
                    : 'Skipped';

              return (
                <TableRow key={row.epg_channel_id} selected={isSelected}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={isSelected}
                      disabled={isDisabled}
                      onChange={() => onToggleRow(row)}
                      inputProps={{ 'aria-label': `select match row ${row.epg_channel_name}` }}
                    />
                  </TableCell>
                  <TableCell>{row.epg_channel_name}</TableCell>
                  <TableCell>{row.best_match_type ? formatMatchLabel(row.best_match_type) : 'No match'}</TableCell>
                  <TableCell>{row.is_creatable && row.best_match_confidence ? formatMatchLabel(row.best_match_confidence) : '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={statusLabel}
                      color={row.is_creatable ? 'success' : row.existing_tv_channel_id ? 'default' : 'warning'}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              );
            })}
            {filteredRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No rows match this filter
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </TableContainer>
    )}
  </Box>
);

export default EPGMatchAnalysisPanel;
