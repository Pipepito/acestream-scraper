import { useSnackbar } from '../hooks/useSnackbar';
import { getErrorMessage } from '../utils/errorUtils';
import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
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
import GuideRecordingSelector from '../components/recordings/GuideRecordingSelector';
import { useConfirm } from '../components/ConfirmDialog';

interface StringMappingFormData {
  search_pattern: string;
  is_exclusion: boolean;
}

const EPGChannelDetail: React.FC = () => {
  const tUi = useUiText();
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
  const { snackbar, showSnackbar, closeSnackbar } = useSnackbar();

  const { data: channel, isLoading: isLoadingChannel, error: channelError } = useEPGChannel(channelId);
  const { data: stringMappings, isLoading: isLoadingMappings, error: stringMappingsError } = useEPGStringMappings(channelId);
  const { data: tvChannels, isLoading: isLoadingTVChannels, error: tvChannelsError } = useTVChannelCatalog();

  const { mutateAsync: addStringMapping } = useAddEPGStringMapping(channelId);
  const { mutateAsync: deleteStringMapping } = useDeleteEPGStringMapping(channelId);
  const { mutateAsync: mapChannel } = useMapEPGChannel();
  const { mutateAsync: createTVChannel, isPending: isCreatingTVChannel } = useCreateTVChannel();

  const selectedMappedChannel = tvChannels?.find((tvChannel: TVChannel) => tvChannel.id === selectedTVChannel) || null;

  const handleAddStringMapping = async () => {
    const trimmedPattern = stringMappingFormData.search_pattern.trim();
    try {
      await addStringMapping({ pattern: trimmedPattern, isExclusion: stringMappingFormData.is_exclusion });
      showSnackbar(() => (uiText("String mapping added successfully")), 'success');
      setOpenStringMappingDialog(false);
      setStringMappingFormData({ search_pattern: '', is_exclusion: false });
    } catch (error) {
      showSnackbar(() => (getErrorMessage(error)), 'error');
    }
  };

  const handleDeleteStringMapping = async (mapping: EPGStringMapping) => {
    const ok = await confirm(() => ({
      title: uiText("Delete the rule “{{pattern}}”?", { pattern: mapping.search_pattern }),
      body: uiText("Matching stops using this pattern from the next EPG refresh."),
      confirmLabel: uiText("Delete"),
      danger: true,
    }));
    if (!ok) return;
    try {
      await deleteStringMapping(mapping.id);
      showSnackbar(() => (uiText("String mapping deleted successfully")), 'success');
    } catch (error) {
      showSnackbar(() => (getErrorMessage(error)), 'error');
    }
  };

  const handleMapToTVChannel = async () => {
    if (!selectedTVChannel || isLoadingTVChannels || tvChannelsError || !tvChannels?.length) return;
    try {
      await mapChannel({ epg_channel_id: channelId, tv_channel_id: selectedTVChannel });
      showSnackbar(() => (uiText("Channel mapped successfully")), 'success');
      setOpenMappingDialog(false);
      setSelectedTVChannel(null);
    } catch (error) {
      showSnackbar(() => (getErrorMessage(error)), 'error');
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
      showSnackbar(() => (uiText("TV channel created successfully")), 'success');
      setOpenCreateTVDialog(false);
    } catch {
      showSnackbar(() => (uiText("Failed to create TV Channel")), 'error');
    }
  };

  if (isLoadingChannel) {
    return (
      <Box sx={{ width: '100%', p: 3 }} role="status" aria-live="polite">
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          {tUi("Loading EPG channel...")}</Typography>
      </Box>
    );
  }

  if (!channel) {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        <Alert severity="error">{channelError ? tUi("Unable to load the EPG channel right now.") : tUi("EPG channel not found")}</Alert>
      </Box>
    );
  }

  const sourceIds = channel.sources?.map((source) => source.source_id) ?? [channel.epg_source_id];
  const linkedTVChannel = tvChannels?.find((tvChannel: TVChannel) => tvChannel.epg_id === channel.channel_xml_id &&
    (tvChannel.epg_source_id == null || sourceIds.includes(tvChannel.epg_source_id))) || null;

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title={channel.name}
        subtitle={tUi("Guide channel from the EPG sources.")}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" startIcon={<BackIcon />} onClick={() => navigate('/epg?tab=channels')}>
              {tUi("Back")}</Button>
            {linkedTVChannel ? null : (
              <>
                <Button variant="outlined" onClick={() => setOpenMappingDialog(true)}>
                  {tUi("Map to TV Channel")}</Button>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openCreateDialog}>
                  {tUi("Create TV Channel")}</Button>
              </>
            )}
          </Stack>
        }
      />

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap role="group" aria-label={tUi("Guide channel summary")} sx={{ mb: 2 }}>
        <Chip label={tUi("XML ID: {{value0}}", { value0: channel.channel_xml_id })} size="small" variant="outlined" sx={{ fontFamily: 'monospace' }} />
        {channel.language ? <Chip label={tUi("Language: {{value0}}", { value0: channel.language })} size="small" variant="outlined" /> : null}
        {isLoadingTVChannels ? (
          <Chip label={tUi("Checking TV channels…")} size="small" variant="outlined" />
        ) : tvChannelsError ? (
          <Chip label={tUi("TV channels unavailable")} size="small" variant="outlined" color="warning" />
        ) : linkedTVChannel ? (
          <Chip
            component={RouterLink}
            to={`/tv-channels/${linkedTVChannel.id}`}
            clickable
            label={tUi("TV channel: {{value0}}", { value0: linkedTVChannel.name })}
            size="small"
            variant="outlined"
            color="primary"
          />
        ) : (
          <Chip label={tUi("Not linked to a TV channel")} size="small" variant="outlined" color="warning" />
        )}
      </Stack>

      <ContentSection title={tUi("Schedule")}>
        {(channel.sources?.length ?? 0) > 1 ? <Stack spacing={1} sx={{ mb: 2 }}>
          <Typography variant="body2">{tUi("This channel is linked to multiple guides. Choose a source to view its schedule.")}</Typography>
          <Stack direction="row" gap={1} flexWrap="wrap" aria-label={tUi("Guide sources")}>
            {channel.sources?.map((source) => <Button key={source.channel_id} component={RouterLink}
              to={`/epg/channels/${source.channel_id}`} variant={source.channel_id === channelId ? 'contained' : 'outlined'}
              aria-current={source.channel_id === channelId ? 'page' : undefined}>
              {source.name}{source.enabled ? '' : ` (${tUi('Disabled')})`}
            </Button>)}
          </Stack>
        </Stack> : null}
        <GuideRecordingSelector key={channelId} epgChannelId={channelId} sourceId={channel.epg_source_id} xmlId={channel.channel_xml_id} />
      </ContentSection>

      <ContentSection
        title={tUi("String mapping rules")}
        description={tUi("Patterns that decide which scraped channel names match this guide channel.")}
        actions={
          <Button variant="contained" color="primary" startIcon={<AddIcon />} onClick={() => setOpenStringMappingDialog(true)}>
            {tUi("Add String Mapping")}</Button>
        }
      >
        {isLoadingMappings ? (
          <Box sx={{ mb: 2 }} role="status" aria-live="polite">
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2">{tUi("Loading string mapping rules...")}</Typography>
          </Box>
        ) : null}

        {!isLoadingMappings && stringMappingsError ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {tUi("Unable to load string mapping rules right now.")}</Alert>
        ) : null}

        {!stringMappingsError ? (
          <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
            <Table aria-label={tUi("String mapping rules table")} size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{tUi("Pattern")}</TableCell>
                  <TableCell>{tUi("Type")}</TableCell>
                  <TableCell>{tUi("Actions")}</TableCell>
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
                      <Chip label={mapping.is_exclusion ? tUi("Exclusion") : tUi("Inclusion")} color={mapping.is_exclusion ? 'error' : 'success'} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Button color="error" size="small" onClick={() => handleDeleteStringMapping(mapping)} aria-label={tUi("Delete string mapping {{value0}}", { value0: mapping.search_pattern })}>
                        {tUi("Delete")}</Button>
                    </TableCell>
                  </TableRow>
                ))}
                {!stringMappingsError && stringMappings && stringMappings.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center">
                      {tUi("No string mappings found")}</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </TableContainer>
        ) : null}
      </ContentSection>

      <Dialog open={openMappingDialog} onClose={() => setOpenMappingDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{tUi("Map to TV Channel")}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {tUi("Select a TV channel to map this EPG channel to:")}</Typography>
          {isLoadingTVChannels ? (
            <Box sx={{ py: 1 }}>
              <LinearProgress sx={{ mb: 2 }} />
              <Typography variant="body2">{tUi("Loading TV channels...")}</Typography>
            </Box>
          ) : null}
          {!isLoadingTVChannels && tvChannelsError ? <Alert severity="error">{tUi("Unable to load TV channels right now.")}</Alert> : null}
          {!isLoadingTVChannels && !tvChannelsError && tvChannels?.length === 0 ? (
            <Alert severity="info">{tUi("No TV channels are available to map yet.")}</Alert>
          ) : null}
          {!isLoadingTVChannels && !tvChannelsError && (tvChannels?.length || 0) > 0 ? (
            <Stack spacing={2}>
              <Alert severity="info" role="status">
                {selectedMappedChannel ? tUi("Selected TV channel: {{value0}}", { value0: selectedMappedChannel.name }) : tUi("Select one TV channel before confirming the mapping.")}
              </Alert>
              <FormControl component="fieldset" fullWidth>
                <RadioGroup
                  aria-label={tUi("Available TV channels")}
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
                                  {tUi("Category:")}{' '}{tvChannel.category || 'None'}
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
          <Button onClick={() => setOpenMappingDialog(false)}>{tUi("Cancel")}</Button>
          <Button
            onClick={handleMapToTVChannel}
            variant="contained"
            color="primary"
            disabled={!selectedTVChannel || isLoadingTVChannels || Boolean(tvChannelsError) || !tvChannels?.length}
          >
            {tUi("Map Channel")}</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openStringMappingDialog} onClose={() => setOpenStringMappingDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{tUi("Add String Mapping")}</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label={tUi("Search Pattern")}
            fullWidth
            value={stringMappingFormData.search_pattern}
            onChange={(event) => setStringMappingFormData({ ...stringMappingFormData, search_pattern: event.target.value })}
            sx={{ mb: 2 }}
            placeholder={tUi("e.g., ESPN, CNN, etc.")}
          />
          <FormControlLabel
            control={
              <Switch
                checked={stringMappingFormData.is_exclusion}
                onChange={(event) => setStringMappingFormData({ ...stringMappingFormData, is_exclusion: event.target.checked })}
              />
            }
            label={tUi("Is Exclusion Pattern")}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {tUi("Inclusion patterns match channels that should be included. Exclusion patterns match channels that should be excluded.")}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenStringMappingDialog(false)}>{tUi("Cancel")}</Button>
          <Button onClick={handleAddStringMapping} variant="contained" color="primary" disabled={!stringMappingFormData.search_pattern.trim()}>
            {tUi("Add Mapping")}</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openCreateTVDialog} onClose={() => setOpenCreateTVDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{tUi("Create TV Channel from EPG")}</DialogTitle>
        <DialogContent>
          <Box my={2}>
            <TextField name="name" label={tUi("Channel Name")} fullWidth value={createTVForm.name} onChange={(e) => setCreateTVForm((f) => ({ ...f, name: e.target.value }))} required margin="dense" />
            <TextField name="logo_url" label={tUi("Logo URL")} fullWidth value={createTVForm.logo_url} onChange={(e) => setCreateTVForm((f) => ({ ...f, logo_url: e.target.value }))} margin="dense" />
            <TextField name="description" label={tUi("Description")} fullWidth value={createTVForm.description} onChange={(e) => setCreateTVForm((f) => ({ ...f, description: e.target.value }))} margin="dense" multiline rows={2} />
            <TextField name="category" label={tUi("Category")} fullWidth value={createTVForm.category} onChange={(e) => setCreateTVForm((f) => ({ ...f, category: e.target.value }))} margin="dense" />
            <TextField name="country" label={tUi("Country")} fullWidth value={createTVForm.country} onChange={(e) => setCreateTVForm((f) => ({ ...f, country: e.target.value }))} margin="dense" />
            <TextField name="language" label={tUi("Language")} fullWidth value={createTVForm.language} onChange={(e) => setCreateTVForm((f) => ({ ...f, language: e.target.value }))} margin="dense" />
            <TextField name="epg_id" label={tUi("EPG ID")} fullWidth value={channel.channel_xml_id} InputProps={{ readOnly: true }} margin="dense" />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateTVDialog(false)} color="inherit">
            {tUi("Cancel")}</Button>
          <Button onClick={handleCreateTVChannel} color="primary" variant="contained" disabled={!createTVForm.name || isCreatingTVChannel}>
            {tUi("Create")}</Button>
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
