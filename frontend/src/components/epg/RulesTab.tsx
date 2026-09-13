import React, { useState } from 'react';
import {
  Alert,
  Box,
  Chip,
  IconButton,
  LinearProgress,
  Link,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import { Link as RouterLink } from 'react-router-dom';
import { useAllEPGStringMappings, useDeleteGlobalEPGStringMapping } from '../../hooks/useEPG';
import { useConfirm } from '../ConfirmDialog';
import type { EPGStringMapping } from '../../services/epgService';

/** Global include/exclude patterns that decide which scraped names match each guide channel. */
const RulesTab: React.FC = () => {
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  });
  const { data: mappings, isLoading, error } = useAllEPGStringMappings();
  const { mutateAsync: deleteMapping, isPending: isDeleting } = useDeleteGlobalEPGStringMapping();

  const handleDeleteMapping = async (mapping: EPGStringMapping) => {
    const ok = await confirm({
      title: `Delete the rule “${mapping.search_pattern}”?`,
      body: 'Matching stops using this pattern from the next EPG refresh.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await deleteMapping(mapping.id);
      setSnackbar({ open: true, message: `Deleted rule ${mapping.search_pattern}`, severity: 'success' });
    } catch (deleteError) {
      setSnackbar({
        open: true,
        message: `Failed to delete rule ${mapping.search_pattern}: ${deleteError instanceof Error ? deleteError.message : 'Unknown error'}`,
        severity: 'error',
      });
    }
  };

  if (isLoading) {
    return (
      <Box role="status" aria-live="polite">
        <LinearProgress sx={{ mb: 1 }} />
        <Typography variant="body2">Loading rules…</Typography>
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Unable to load the matching rules right now.</Alert>;
  }

  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Rules are added from a guide channel’s page. Include rules make a scraped name match that channel; exclude rules stop a false match.
      </Typography>
      {mappings && mappings.length > 0 ? (
        <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
          <Table size="small" aria-label="Matching rules">
            <TableHead>
              <TableRow>
                <TableCell>Pattern</TableCell>
                <TableCell>Rule</TableCell>
                <TableCell>Guide channel</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mappings.map((mapping) => (
                <TableRow key={mapping.id}>
                  <TableCell sx={{ fontFamily: 'monospace' }}>{mapping.search_pattern}</TableCell>
                  <TableCell>
                    <Chip label={mapping.is_exclusion ? 'Exclude' : 'Include'} color={mapping.is_exclusion ? 'warning' : 'success'} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Link component={RouterLink} to={`/epg/channels/${mapping.epg_channel_id}`}>
                      Channel #{mapping.epg_channel_id}
                    </Link>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Delete rule">
                      <span>
                        <IconButton
                          aria-label={`Delete mapping ${mapping.search_pattern}`}
                          color="error"
                          size="small"
                          onClick={() => handleDeleteMapping(mapping)}
                          disabled={isDeleting}
                        >
                          <DeleteOutlineRoundedIcon fontSize="small" />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Typography color="text.secondary">No rules yet. Open a guide channel and add one when a name does not match.</Typography>
      )}
      {confirmDialog}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((current) => ({ ...current, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar((current) => ({ ...current, open: false }))} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RulesTab;
