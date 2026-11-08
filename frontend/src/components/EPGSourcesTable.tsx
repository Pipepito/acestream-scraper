import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { responsiveTableSx } from '../styles/responsiveTable';
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
import { formatRelativeTime } from '../utils/format';
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
}) => { const tUi = useUiText(); return (
  <TableContainer component={Box} sx={responsiveTableSx}>
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>{tUi("Name")}</TableCell>
          <TableCell>{tUi("URL")}</TableCell>
          <TableCell>{tUi("Status")}</TableCell>
          <TableCell>{tUi("Last Updated")}</TableCell>
          <TableCell>{tUi("Actions")}</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {(sources || []).map((source) => (
          <TableRow key={source.id}>
            <TableCell data-label={uiText("Name")}>{source.name}</TableCell>
            <TableCell data-label="URL">{source.url}</TableCell>
            <TableCell data-label={uiText("Status")}>
              {source.enabled ? (
                <Chip label={tUi("Enabled")} color="success" size="small" />
              ) : (
                <Chip label={tUi("Disabled")} color="default" size="small" />
              )}
              {source.error_count > 0 ? (
                <Typography variant="caption" color="error.main" component="p" sx={{ mt: 0.5, maxWidth: 360, overflowWrap: 'anywhere' }}>
                  {tUi("{{count}} failed refresh", { count: source.error_count })}
                  {source.last_error ? tUi(" · {{value0}}", { value0: source.last_error }) : ''}
                </Typography>
              ) : null}
            </TableCell>
            <TableCell data-label={uiText("Last updated")}>
              {source.last_updated ? (
                formatRelativeTime(source.last_updated)
              ) : (
                tUi('Never')
              )}
            </TableCell>
            <TableCell data-label={uiText("Actions")}>
              <IconButton
                color="primary"
                onClick={() => onRefreshSource(source.id)}
                disabled={refreshingSourceId === source.id}
                aria-label={tUi("Refresh source {{value0}}", { value0: source.name })}
              >
                <RefreshIcon />
              </IconButton>
              <IconButton color="secondary" onClick={() => onEditSource(source)} aria-label={tUi("Edit source {{value0}}", { value0: source.name })}>
                <EditIcon />
              </IconButton>
              <IconButton color="error" onClick={() => onDeleteSource(source.id)} aria-label={tUi("Delete source {{value0}}", { value0: source.name })}>
                <DeleteIcon />
              </IconButton>
            </TableCell>
          </TableRow>
        ))}
        {sources && sources.length === 0 && (
          <TableRow>
            <TableCell colSpan={5} align="center">
              {tUi("No EPG sources found")}</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  </TableContainer>
); };

export default EPGSourcesTable;
