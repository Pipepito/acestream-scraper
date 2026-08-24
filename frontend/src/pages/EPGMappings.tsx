import React, { useState } from 'react';
import {
  Alert,
  Box,
  Chip,
  CircularProgress,
  IconButton,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { useAllEPGStringMappings, useDeleteGlobalEPGStringMapping } from '../hooks/useEPG';

const EPGMappings: React.FC = () => {
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error';
  }>({
    open: false,
    message: '',
    severity: 'success',
  });

  const { data: mappings, isLoading, error } = useAllEPGStringMappings();
  const { mutateAsync: deleteMapping, isPending: isDeleting } = useDeleteGlobalEPGStringMapping();

  const handleDeleteMapping = async (id: number, pattern: string) => {
    try {
      await deleteMapping(id);
      setSnackbar({
        open: true,
        message: `Deleted mapping ${pattern}`,
        severity: 'success',
      });
    } catch (deleteError) {
      setSnackbar({
        open: true,
        message: `Failed to delete mapping ${pattern}: ${deleteError instanceof Error ? deleteError.message : 'Unknown error'}`,
        severity: 'error',
      });
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{`EPG mappings error: ${error.toString()}`}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <PageHeader
        title="EPG Mappings"
        subtitle="Review and remove global include and exclude rules when channel matching looks wrong or outdated."
      />

      <ContentSection
        title="Global mapping rules"
        description="Use this table to review current mapping patterns and remove outdated rules without opening individual channels."
      >
        {mappings && mappings.length > 0 ? (
          <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Pattern</TableCell>
                  <TableCell>Rule type</TableCell>
                  <TableCell>EPG channel ID</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mappings.map((mapping) => (
                  <TableRow key={mapping.id}>
                    <TableCell>{mapping.search_pattern}</TableCell>
                    <TableCell>
                      <Chip
                        label={mapping.is_exclusion ? 'Exclude' : 'Include'}
                        color={mapping.is_exclusion ? 'warning' : 'success'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{mapping.epg_channel_id}</TableCell>
                    <TableCell align="right">
                      <IconButton
                        aria-label={`Delete mapping ${mapping.search_pattern}`}
                        color="error"
                        onClick={() => handleDeleteMapping(mapping.id, mapping.search_pattern)}
                        disabled={isDeleting}
                      >
                        <DeleteOutlineRoundedIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography color="text.secondary">No global mappings exist yet.</Typography>
        )}
      </ContentSection>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((current) => ({ ...current, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar((current) => ({ ...current, open: false }))}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EPGMappings;
