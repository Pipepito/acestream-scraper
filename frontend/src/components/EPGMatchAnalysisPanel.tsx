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

    <Alert severity="info" sx={{ mb: 2 }}>Select only the matches you have reviewed. Similar names need particular care. To resolve competing guide sources, select a source and analyze again. Automatic matching is optional in Settings → Automation.</Alert>
    {analysis.rows.some(row => (row.ambiguous_count ?? 0) > 0) ? <Alert severity="warning" sx={{ mb: 2 }}>Some streams match more than one guide channel equally well. They have not been selected or assigned.</Alert> : null}
    {analysis.summary.matched_epg_channels === 0 ? <Alert severity="info" sx={{ mb: 2 }}>No matches met the current strictness.</Alert> : null}
    {analysis.rows.length === 0 ? (
      <Typography>No guide channels are available. Add and refresh an EPG source first.</Typography>
    ) : (
      <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
        <Table size="small" sx={{
          display: { xs: 'block', sm: 'table' },
          '& thead': { display: { xs: 'none', sm: 'table-header-group' } },
          '& tbody': { display: { xs: 'block', sm: 'table-row-group' } },
          '& tbody tr': { display: { xs: 'grid', sm: 'table-row' }, gridTemplateColumns: '40px minmax(0, 1fr)', borderBottom: { xs: 1, sm: 0 }, borderColor: 'divider', py: { xs: 1, sm: 0 } },
          '& tbody td': { gridColumn: '2', borderBottom: { xs: 0, sm: 1 }, borderColor: 'divider', overflowWrap: 'anywhere' },
          '& tbody td:first-of-type': { gridColumn: '1', gridRow: '1 / span 5' },
          '& td[data-label]::before': { content: 'attr(data-label)', display: { xs: 'block', sm: 'none' }, typography: 'caption', color: 'text.secondary', mb: 0.5 },
        }}>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">Select</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Proposed streams</TableCell>
              <TableCell>Match Type</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredRows.map((row) => {
              const isSelected = selectedRowIds.includes(row.epg_channel_id);
              const isDisabled = !(row.can_apply ?? row.is_creatable);
              const statusLabel = row.existing_tv_channel_id
                ? row.can_apply ? 'Add streams' : 'Existing channel preserved'
                : row.candidate_count === 0
                  ? (row.ambiguous_count ?? 0) > 0 ? 'Ambiguous' : 'No candidate'
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
                  <TableCell data-label="Guide channel"><Typography variant="body2">{row.epg_channel_name}</Typography><Typography variant="caption" color="text.secondary">{row.epg_source_name} · {row.epg_channel_xml_id}</Typography></TableCell>
                  <TableCell data-label="Proposed streams">{row.candidates.map(candidate => <Typography key={candidate.acestream_channel_id} variant="body2">{candidate.name}</Typography>)}</TableCell>
                  <TableCell data-label="Match type">{row.best_match_type ? formatMatchLabel(row.best_match_type) : 'No match'}</TableCell>
                  <TableCell data-label="Confidence">{row.is_creatable && row.best_match_confidence ? formatMatchLabel(row.best_match_confidence) : '-'}</TableCell>
                  <TableCell data-label="Status">
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
                <TableCell colSpan={6} align="center">
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
