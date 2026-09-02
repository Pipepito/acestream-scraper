import React, { useState } from 'react';
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  LinearProgress,
  Radio,
  RadioGroup,
  Snackbar,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { Add as AddIcon, ArrowBack as BackIcon } from '@mui/icons-material';
import {
  useEPGChannel,
  useEPGStringMappings,
  useAddEPGStringMapping,
  useDeleteEPGStringMapping,
  useMapEPGChannel,
} from '../hooks/useEPG';
import { useCreateTVChannel, useTVChannelCatalog } from '../hooks/useTVChannels';
import { EPGStringMapping } from '../services/epgService';
import { TVChannel } from '../types/tvChannelTypes';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import ScheduleView from '../components/epg/ScheduleView';
import { useConfirm } from '../components/ConfirmDialog';

interface StringMappingFormData {
  search_pattern: string;
  is_exclusion: boolean;
}

const EPGChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const channelId = parseInt(id || '0', 10);
  const { confirm, dialog: confirmDialog } = useConfirm();

  const [openMappingDialog, setOpenMappingDialog] = useState(false);
  const [openStringMappingDialog, setOpenStringMappingDialog] = useState(false);
  const [openCreateTVDialog, setOpenCreateTVDialog] = useState(false);
  const [selectedTVChannel, setSelectedTVChannel] = useState<number | null>(null);
  const [stringMappingFormData, setStringMappingFormData] = useState<StringMappingFormData>({ search_pattern: '', is_exclusion: false });
  const [createTVForm, setCreateTVForm] = useState({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    epg_id: '',
    is_active: true,
    is_favorite: false,
  });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });

  const { data: channel, isLoading: isLoadingChannel, error: channelError } = useEPGChannel(channelId);
  const { data: stringMappings, isLoading: isLoadingMappings, error: stringMappingsError } = useEPGStringMappings(channelId);
  const { data: tvChannels, isLoading: isLoadingTVChannels, error: tvChannelsError } = useTVChannelCatalog();

  const { mutateAsync: addStringMapping } = useAddEPGStringMapping(channelId);
  const { mutateAsync: deleteStringMapping } = useDeleteEPGStringMapping(channelId);
  const { mutateAsync: mapChannel } = useMapEPGChannel();
  const { mutateAsync: createTVChannel, isPending: isCreatingTVChannel } = useCreateTVChannel();

  const selectedMappedChannel = tvChannels?.find((tvChannel: TVChannel) => tvChannel.id === selectedTVChannel) || null;

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };
  const closeSnackbar = () => setSnackbar((prev) => ({ ...prev, open: false }));

  const handleAddStringMapping = async () => {
    const trimmedPattern = stringMappingFormData.search_pattern.trim();
    try {
      await addStringMapping({ pattern: trimmedPattern, isExclusion: stringMappingFormData.is_exclusion });
      showSnackbar('String mapping added successfully', 'success');
      setOpenStringMappingDialog(false);
      setStringMappingFormData({ search_pattern: '', is_exclusion: false });
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleDeleteStringMapping = async (mapping: EPGStringMapping) => {
    const ok = await confirm({
      title: `Delete the rule “${mapping.search_pattern}”?`,
      body: 'Matching stops using this pattern from the next EPG refresh.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await deleteStringMapping(mapping.id);
      showSnackbar('String mapping deleted successfully', 'success');
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleMapToTVChannel = async () => {
    if (!selectedTVChannel || isLoadingTVChannels || tvChannelsError || !tvChannels?.length) return;
    try {
      await mapChannel({ epg_channel_id: channelId, tv_channel_id: selectedTVChannel });
      showSnackbar('Channel mapped successfully', 'success');
      setOpenMappingDialog(false);
      setSelectedTVChannel(null);
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const openCreateDialog = () => {
    if (!channel) return;
    setCreateTVForm((prev) => ({
      ...prev,
      name: prev.name || channel.name,
      logo_url: prev.logo_url || channel.icon_url || '',
      language: prev.language || channel.language || '',
      epg_id: channel.channel_xml_id,
    }));
    setOpenCreateTVDialog(true);
  };

  const handleCreateTVChannel = async () => {
    if (!channel) return;
    try {
      await createTVChannel({ ...createTVForm, epg_id: channel.channel_xml_id });
      showSnackbar('TV channel created successfully', 'success');
      setOpenCreateTVDialog(false);
    } catch {
      showSnackbar('Failed to create TV Channel', 'error');
    }
  };

  if (isLoadingChannel) {
    return (
      <Box sx={{ width: '100%', p: 3 }} role="status" aria-live="polite">
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading EPG channel...
        </Typography>
      </Box>
    );
  }

  if (!channel) {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        <Alert severity="error">{channelError ? 'Unable to load the EPG channel right now.' : 'EPG channel not found'}</Alert>
      </Box>
    );
  }

  const linkedTVChannel = tvChannels?.find((tvChannel: TVChannel) => tvChannel.epg_id === channel.channel_xml_id) || null;

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title={channel.name}
        subtitle="Guide channel from the EPG sources."
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" startIcon={<BackIcon />} onClick={() => navigate('/epg?tab=channels')}>
              Back
            </Button>
            {linkedTVChannel ? null : (
              <>
                <Button variant="outlined" onClick={() => setOpenMappingDialog(true)}>
                  Map to TV Channel
                </Button>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openCreateDialog}>
                  Create TV Channel
                </Button>
              </>
            )}
          </Stack>
        }
      />

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap role="group" aria-label="Guide channel summary" sx={{ mb: 2 }}>
        <Chip label={`XML ID: ${channel.channel_xml_id}`} size="small" variant="outlined" sx={{ fontFamily: 'monospace' }} />
        {channel.language ? <Chip label={`Language: ${channel.language}`} size="small" variant="outlined" /> : null}
        {isLoadingTVChannels ? (
          <Chip label="Checking TV channels…" size="small" variant="outlined" />
        ) : tvChannelsError ? (
          <Chip label="TV channels unavailable" size="small" variant="outlined" color="warning" />
        ) : linkedTVChannel ? (
          <Chip
            component={RouterLink}
            to={`/tv-channels/${linkedTVChannel.id}`}
            clickable
            label={`TV channel: ${linkedTVChannel.name}`}
            size="small"
            variant="outlined"
            color="primary"
          />
        ) : (
          <Chip label="Not linked to a TV channel" size="small" variant="outlined" color="warning" />
        )}
      </Stack>

      <ContentSection title="Schedule">
        <ScheduleView epgChannelId={channelId} />
      </ContentSection>

      <ContentSection
        title="String mapping rules"
        description="Patterns that decide which scraped channel names match this guide channel."
        actions={
          <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={() => setOpenStringMappingDialog(true)}>
            Add String Mapping
          </Button>
        }
      >
        {isLoadingMappings ? (
          <Box sx={{ mb: 2 }} role="status" aria-live="polite">
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2">Loading string mapping rules...</Typography>
          </Box>
        ) : null}

        {!isLoadingMappings && stringMappingsError ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            Unable to load string mapping rules right now.
          </Alert>
        ) : null}

        {!stringMappingsError ? (
          <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
            <Table aria-label="String mapping rules table" size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Pattern</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {stringMappings?.map((mapping: EPGStringMapping) => (
                  <TableRow key={mapping.id}>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {mapping.search_pattern}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={mapping.is_exclusion ? 'Exclusion' : 'Inclusion'} color={mapping.is_exclusion ? 'error' : 'success'} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Button color="error" size="small" onClick={() => handleDeleteStringMapping(mapping)} aria-label={`Delete string mapping ${mapping.search_pattern}`}>
                        Delete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!stringMappingsError && stringMappings && stringMappings.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center">
                      No string mappings found
                    </TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </TableContainer>
        ) : null}
      </ContentSection>

      <Dialog open={openMappingDialog} onClose={() => setOpenMappingDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Map to TV Channel</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Select a TV channel to map this EPG channel to:
          </Typography>
          {isLoadingTVChannels ? (
            <Box sx={{ py: 1 }}>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography variant="body2">Loading TV channels...</Typography>
            </Box>
          ) : null}
          {!isLoadingTVChannels && tvChannelsError ? <Alert severity="error">Unable to load TV channels right now.</Alert> : null}
          {!isLoadingTVChannels && !tvChannelsError && tvChannels?.length === 0 ? (
            <Alert severity="info">No TV channels are available to map yet.</Alert>
          ) : null}
          {!isLoadingTVChannels && !tvChannelsError && (tvChannels?.length || 0) > 0 ? (
            <Stack spacing={2}>
              <Alert severity="info" role="status">
                {selectedMappedChannel ? `Selected TV channel: ${selectedMappedChannel.name}` : 'Select one TV channel before confirming the mapping.'}
              </Alert>
              <FormControl component="fieldset" fullWidth>
                <RadioGroup
                  aria-label="Available TV channels"
                  name="available-tv-channels"
                  value={selectedTVChannel?.toString() || ''}
                  onChange={(_event, value) => setSelectedTVChannel(Number(value))}
                >
                  <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                    {(tvChannels || []).map((tvChannel: TVChannel) => {
                      const isSelected = tvChannel.id === selectedTVChannel;
                      return (
                        <Box
                          key={tvChannel.id}
                          sx={{
                            p: 1.5,
                            mb: 1,
                            border: 1,
                            borderColor: isSelected ? 'primary.main' : 'divider',
                            borderRadius: 2,
                            bgcolor: isSelected ? 'action.selected' : 'background.paper',
                          }}
                        >
                          <FormControlLabel
                            value={tvChannel.id.toString()}
                            control={<Radio />}
                            label={
                              <Box>
                                <Typography variant="body1" fontWeight="bold">
                                  {tvChannel.name}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Category: {tvChannel.category || 'None'}
                                </Typography>
                              </Box>
                            }
                            sx={{ alignItems: 'flex-start', m: 0, width: '100%' }}
                          />
                        </Box>
                      );
                    })}
                  </Box>
                </RadioGroup>
              </FormControl>
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenMappingDialog(false)}>Cancel</Button>
          <Button
            onClick={handleMapToTVChannel}
            variant="contained"
            color="primary"
            disabled={!selectedTVChannel || isLoadingTVChannels || Boolean(tvChannelsError) || !tvChannels?.length}
          >
            Map Channel
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openStringMappingDialog} onClose={() => setOpenStringMappingDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add String Mapping</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Search Pattern"
            fullWidth
            value={stringMappingFormData.search_pattern}
            onChange={(event) => setStringMappingFormData({ ...stringMappingFormData, search_pattern: event.target.value })}
            sx={{ mb: 2 }}
            placeholder="e.g., ESPN, CNN, etc."
          />
          <FormControlLabel
            control={
              <Switch
                checked={stringMappingFormData.is_exclusion}
                onChange={(event) => setStringMappingFormData({ ...stringMappingFormData, is_exclusion: event.target.checked })}
              />
            }
            label="Is Exclusion Pattern"
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Inclusion patterns match channels that should be included. Exclusion patterns match channels that should be excluded.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenStringMappingDialog(false)}>Cancel</Button>
          <Button onClick={handleAddStringMapping} variant="contained" color="primary" disabled={!stringMappingFormData.search_pattern.trim()}>
            Add Mapping
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openCreateTVDialog} onClose={() => setOpenCreateTVDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create TV Channel from EPG</DialogTitle>
        <DialogContent>
          <Box my={2}>
            <TextField name="name" label="Channel Name" fullWidth value={createTVForm.name} onChange={(e) => setCreateTVForm((f) => ({ ...f, name: e.target.value }))} required margin="dense" />
            <TextField name="logo_url" label="Logo URL" fullWidth value={createTVForm.logo_url} onChange={(e) => setCreateTVForm((f) => ({ ...f, logo_url: e.target.value }))} margin="dense" />
            <TextField name="description" label="Description" fullWidth value={createTVForm.description} onChange={(e) => setCreateTVForm((f) => ({ ...f, description: e.target.value }))} margin="dense" multiline rows={2} />
            <TextField name="category" label="Category" fullWidth value={createTVForm.category} onChange={(e) => setCreateTVForm((f) => ({ ...f, category: e.target.value }))} margin="dense" />
            <TextField name="country" label="Country" fullWidth value={createTVForm.country} onChange={(e) => setCreateTVForm((f) => ({ ...f, country: e.target.value }))} margin="dense" />
            <TextField name="language" label="Language" fullWidth value={createTVForm.language} onChange={(e) => setCreateTVForm((f) => ({ ...f, language: e.target.value }))} margin="dense" />
            <TextField name="epg_id" label="EPG ID" fullWidth value={channel.channel_xml_id} InputProps={{ readOnly: true }} margin="dense" />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateTVDialog(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleCreateTVChannel} color="primary" variant="contained" disabled={!createTVForm.name || isCreatingTVChannel}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {confirmDialog}

      <Snackbar open={snackbar.open} onClose={closeSnackbar} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert onClose={closeSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EPGChannelDetail;
