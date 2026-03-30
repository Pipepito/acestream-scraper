import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
  Grid,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Pagination,
  Stack,
  FormControl,
  Radio,
  RadioGroup,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Tv as TvIcon,
  Add as AddIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { alpha, useTheme } from '@mui/material/styles';
import { format, parseISO } from 'date-fns';
import {
  useEPGChannel,
  useEPGPrograms,
  useEPGStringMappings,
  useAddEPGStringMapping,
  useDeleteEPGStringMapping,
  useMapEPGChannel,
} from '../hooks/useEPG';
import { useCreateTVChannel, useTVChannelCatalog } from '../hooks/useTVChannels';
import { EPGProgram, EPGStringMapping } from '../services/epgService';
import { TVChannel } from '../types/tvChannelTypes';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import { getLocalISODate, getRelativeLocalISODate } from '../utils/dateUtils';

interface StringMappingFormData {
  search_pattern: string;
  is_exclusion: boolean;
}

const EPGChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const channelId = parseInt(id || '0', 10);

  // State management
  const [currentPage, setCurrentPage] = useState(1);
  const [programsPerPage] = useState(50);
  const [dateRange, setDateRange] = useState({
    start: getLocalISODate(),
    end: getRelativeLocalISODate(7)
  });

  // Dialog states
  const [openMappingDialog, setOpenMappingDialog] = useState(false);
  const [openStringMappingDialog, setOpenStringMappingDialog] = useState(false);
  const [openCreateTVDialog, setOpenCreateTVDialog] = useState(false);
  const [selectedTVChannel, setSelectedTVChannel] = useState<number | null>(null);
  const [stringMappingFormData, setStringMappingFormData] = useState<StringMappingFormData>({
    search_pattern: '',
    is_exclusion: false
  });
  const [createTVForm, setCreateTVForm] = useState({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    epg_id: '',
    is_active: true,
    is_favorite: false
  });
  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'warning' | 'info'
  });

  // API hooks
  const { data: channel, isLoading: isLoadingChannel, error: channelError } = useEPGChannel(channelId);
  const { data: programs, isLoading: isLoadingPrograms, error: programsError } = useEPGPrograms(
    channelId,
    dateRange.start,
    dateRange.end
  );
  const { data: stringMappings, isLoading: isLoadingMappings, error: stringMappingsError } = useEPGStringMappings(channelId);
  const {
    data: tvChannels,
    isLoading: isLoadingTVChannels,
    error: tvChannelsError,
  } = useTVChannelCatalog();

  // Mutations
  const { mutateAsync: addStringMapping } = useAddEPGStringMapping(channelId);
  const { mutateAsync: deleteStringMapping } = useDeleteEPGStringMapping(channelId);
  const { mutateAsync: mapChannel } = useMapEPGChannel();
  const { mutateAsync: createTVChannel, isLoading: isCreatingTVChannel } = useCreateTVChannel();

  const selectedMappedChannel = tvChannels?.find((tvChannel: TVChannel) => tvChannel.id === selectedTVChannel) || null;

  // Pagination
  const totalPages = Math.ceil((programs?.length || 0) / programsPerPage);
  const paginatedPrograms = programs?.slice(
    (currentPage - 1) * programsPerPage,
    currentPage * programsPerPage
  );

  const handlePageChange = (event: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  };

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    setDateRange(prev => ({
      ...prev,
      [field]: value
    }));
    setCurrentPage(1); // Reset to first page when date changes
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setSnackbar({
      open: true,
      message,
      severity
    });
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // String mapping handlers
  const handleAddStringMapping = async () => {
    const trimmedPattern = stringMappingFormData.search_pattern.trim();

    try {
      await addStringMapping({
        pattern: trimmedPattern,
        isExclusion: stringMappingFormData.is_exclusion
      });
      showSnackbar('String mapping added successfully', 'success');
      setOpenStringMappingDialog(false);
      setStringMappingFormData({ search_pattern: '', is_exclusion: false });
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleDeleteStringMapping = async (mappingId: number) => {
    if (window.confirm('Are you sure you want to delete this string mapping?')) {
      try {
        await deleteStringMapping(mappingId);
        showSnackbar('String mapping deleted successfully', 'success');
      } catch (error) {
        showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      }
    }
  };

  // TV channel mapping handlers
  const handleMapToTVChannel = async () => {
    if (!selectedTVChannel || isLoadingTVChannels || tvChannelsError || !tvChannels?.length) return;

    try {
      await mapChannel({
        epg_channel_id: channelId,
        tv_channel_id: selectedTVChannel
      });
      showSnackbar('Channel mapped successfully', 'success');
      setOpenMappingDialog(false);
      setSelectedTVChannel(null);
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleCreateTVChannel = async () => {
    if (!channel) {
      return;
    }

    try {
      await createTVChannel({ ...createTVForm, epg_id: channel.channel_xml_id });
      showSnackbar('TV channel created successfully', 'success');
      setOpenCreateTVDialog(false);
    } catch (_error) {
      showSnackbar('Failed to create TV Channel', 'error');
    }
  };

  const formatDateTime = (dateTimeString: string) => {
    try {
      return format(parseISO(dateTimeString), 'PPP p');
    } catch (error) {
      return dateTimeString;
    }
  };

  const formatDuration = (startTime: string, endTime: string) => {
    try {
      const start = parseISO(startTime);
      const end = parseISO(endTime);
      const durationMs = end.getTime() - start.getTime();
      const hours = Math.floor(durationMs / (1000 * 60 * 60));
      const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      } else {
        return `${minutes}m`;
      }
    } catch (error) {
      return '-';
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
        <Alert severity="error">
          {channelError ? 'Unable to load the EPG channel right now.' : 'EPG channel not found'}
        </Alert>
      </Box>
    );
  }

  const inferredLinkedTVChannel =
    tvChannels?.find((tvChannel: TVChannel) => tvChannel.epg_id === channel.channel_xml_id) || null;
  const hasRelationshipLoading = isLoadingTVChannels || isLoadingPrograms;
  const hasRelationshipError = Boolean(tvChannelsError || programsError);
  const hasMappingChoices = (tvChannels?.length || 0) > 0;
  const visibleProgramCount = programs?.length || 0;
  const hasVisiblePrograms = visibleProgramCount > 0;
  const stringMappingCount = stringMappings?.length || 0;
  const stringMappingSupport = isLoadingMappings
    ? 'String mapping rules are still loading for this source.'
    : stringMappingsError
      ? 'String mapping rules need attention before this summary can suggest tuning cleanup.'
      : stringMappingCount > 0
        ? `${stringMappingCount} string mapping rule${stringMappingCount === 1 ? '' : 's'} ready for tuning.`
        : 'No string mapping rules are set yet.';

  const relationshipState = hasRelationshipLoading
    ? 'Checking loaded TV channel relationships'
    : hasRelationshipError
      ? 'Relationship evidence is incomplete right now'
      : inferredLinkedTVChannel
        ? hasVisiblePrograms
          ? 'An inferred linked TV channel is available for review and tuning'
          : `Linked TV channel found in the loaded catalog: ${inferredLinkedTVChannel.name}`
        : 'No linked TV channel found in the loaded catalog yet';

  const nextStepLabel = hasRelationshipLoading
    ? 'Wait for the TV catalog and schedule window to finish loading before choosing the next relationship action.'
    : hasRelationshipError
      ? 'Resolve the TV catalog or schedule loading error before deciding whether to map, create, or tune this source.'
      : inferredLinkedTVChannel
        ? hasVisiblePrograms
          ? 'Review the schedule evidence and string rules before treating this pairing as final.'
          : 'Review the selected date range or schedule ingestion before adjusting mapping rules.'
        : hasMappingChoices
          ? 'Map this source to an existing TV channel before tuning schedule rules.'
          : 'Create a TV channel first so this source has a destination for mapping.';

  const relationshipMetric = hasRelationshipLoading
    ? 'TV catalog and schedule evidence are still loading.'
    : hasRelationshipError
      ? 'TV catalog or schedule evidence is unavailable right now.'
      : inferredLinkedTVChannel
        ? `${hasVisiblePrograms ? `${visibleProgramCount} visible program${visibleProgramCount === 1 ? '' : 's'}` : 'No visible programs'} in the selected date range.`
        : hasMappingChoices
          ? `${tvChannels?.length || 0} TV channel option${(tvChannels?.length || 0) === 1 ? '' : 's'} available for mapping.`
          : 'No TV channel options are loaded yet.';

  const relationshipSupport = `XML ID ${channel.channel_xml_id} is loaded for review. ${hasRelationshipLoading ? 'Schedule and TV catalog evidence are still arriving.' : hasRelationshipError ? 'Schedule or TV catalog evidence needs attention before this summary can recommend a confident relationship action.' : hasVisiblePrograms ? `${visibleProgramCount} program${visibleProgramCount === 1 ? '' : 's'} visible in the selected date range.` : 'No programs are visible in the selected date range.'} ${stringMappingSupport}`;

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title={channel.name}
        subtitle="Review channel metadata, inspect schedule windows, and control mapping from a single operational detail route."
        actions={
          <>
            <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={() => navigate('/epg')} aria-label="Back to EPG management">
              Back to EPG Management
            </Button>
            <Button
              variant="outlined"
              startIcon={<LinkIcon />}
              onClick={() => setOpenMappingDialog(true)}
              size="small"
            >
              Map to TV Channel
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setCreateTVForm({
                  name: channel.name,
                  logo_url: channel.icon_url || '',
                  description: '',
                  category: '',
                  country: '',
                  language: channel.language || '',
                  epg_id: channel.channel_xml_id || '',
                  is_active: true,
                  is_favorite: false
                });
                setOpenCreateTVDialog(true);
              }}
              size="small"
            >
              Create TV Channel
            </Button>
          </>
        }
      />

      <Box
        sx={{
          mb: 3,
          p: { xs: 2, md: 2.5 },
          borderRadius: 2.5,
          bgcolor: theme.appTokens.hero.bg,
          border: `1px solid ${theme.appTokens.hero.border}`,
          backgroundImage: theme.appTokens.hero.spotlight,
        }}
      >
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5, justifyContent: 'space-between' }}>
          <Stack spacing={1} sx={{ minWidth: 0, flex: '1 1 520px', maxWidth: 760 }}>
            <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent, mb: 1 }}>
              Relationship summary
            </Typography>
            <Typography variant="h4" sx={{ letterSpacing: '-0.03em', mb: 1 }}>
              EPG source: {channel.name}
            </Typography>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: alpha(theme.appTokens.shell.accent, 0.08),
                border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}`,
              }}
            >
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                Relationship state
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {relationshipState}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {relationshipMetric}
              </Typography>
            </Box>

            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: theme.appTokens.surface.panel,
                border: `1px solid ${theme.appTokens.surface.border}`,
              }}
            >
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                Next step
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                {nextStepLabel}
              </Typography>
            </Box>

            <Typography variant="body2" color="text.secondary">
              {relationshipSupport}
            </Typography>
          </Stack>
        </Box>
      </Box>

      <ContentSection title="Channel Summary" description="Confirm identity details before mapping or filtering program results.">
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              {channel.icon_url && (
                <Box
                  component="img"
                  src={channel.icon_url}
                  alt={channel.name}
                  sx={{ height: 50, marginRight: 2 }}
                />
              )}
              <Box>
                <Typography variant="body1" fontWeight="bold">
                  {channel.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  XML ID: {channel.channel_xml_id}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Language: {channel.language || 'Unknown'}
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Stack direction={{ xs: 'row', md: 'column' }} spacing={1}>
              <Chip icon={<TvIcon />} label="EPG channel" size="small" color="info" />
              <Chip label={`Programs loaded: ${programs?.length || 0}`} size="small" />
            </Stack>
          </Grid>
        </Grid>
      </ContentSection>

      <ContentSection title="Program Schedule" description="Use the date window to narrow the visible schedule before reviewing detailed rows.">
        <Box sx={{ mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                label="Start Date"
                type="date"
                value={dateRange.start}
                onChange={(e) => handleDateRangeChange('start', e.target.value)}
                fullWidth
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="End Date"
                type="date"
                value={dateRange.end}
                onChange={(e) => handleDateRangeChange('end', e.target.value)}
                fullWidth
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Total Programs: {programs?.length || 0}
              </Typography>
            </Grid>
          </Grid>
        </Box>

        {isLoadingPrograms ? (
          <Box sx={{ mb: 2 }} role="status" aria-live="polite">
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2">Loading schedule for the selected date range...</Typography>
          </Box>
        ) : null}

        {!isLoadingPrograms && programsError ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            Unable to load the schedule for this date range right now.
          </Alert>
        ) : null}

        {!programsError ? (
          <TableContainer component={Box} sx={{ overflowX: 'auto' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Start Time</TableCell>
                <TableCell>End Time</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Subtitle</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Description</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedPrograms?.map((program: EPGProgram) => (
                <TableRow key={program.id}>
                  <TableCell>{formatDateTime(program.start_time)}</TableCell>
                  <TableCell>{formatDateTime(program.end_time)}</TableCell>
                  <TableCell>{formatDuration(program.start_time, program.end_time)}</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {program.title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {program.subtitle ? (
                      <Typography variant="body2" color="text.secondary">
                        {program.subtitle}
                      </Typography>
                    ) : null}
                  </TableCell>
                  <TableCell>
                    {program.category ? <Chip label={program.category} size="small" /> : null}
                  </TableCell>
                  <TableCell>
                    {program.description ? (
                      <Typography variant="body2" color="text.secondary">
                        {program.description.length > 100
                          ? `${program.description.substring(0, 100)}...`
                          : program.description}
                      </Typography>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
               {!programsError && programs && programs.length === 0 ? (
                 <TableRow>
                   <TableCell colSpan={7} align="center">
                     No programs found for the selected date range
                  </TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
          </TableContainer>
        ) : null}

        {totalPages > 1 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Stack spacing={2}>
              <Pagination
                count={totalPages}
                page={currentPage}
                onChange={handlePageChange}
                color="primary"
                showFirstButton
                showLastButton
              />
            </Stack>
          </Box>
        ) : null}
      </ContentSection>

      <ContentSection
        title="String Mapping Rules"
        description="Maintain inclusion and exclusion patterns with explicit actions and visible rule types."
        actions={
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => setOpenStringMappingDialog(true)}
          >
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
          <Table>
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
                    <Chip
                      label={mapping.is_exclusion ? 'Exclusion' : 'Inclusion'}
                      color={mapping.is_exclusion ? 'error' : 'success'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Button
                      color="error"
                      onClick={() => handleDeleteStringMapping(mapping.id)}
                      aria-label={`Delete string mapping ${mapping.search_pattern}`}
                    >
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

      {/* TV Channel Mapping Dialog */}
      <Dialog
        open={openMappingDialog}
        onClose={() => setOpenMappingDialog(false)}
        maxWidth="md"
        fullWidth
      >
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

          {!isLoadingTVChannels && tvChannelsError ? (
            <Alert severity="error">Unable to load TV channels right now.</Alert>
          ) : null}

          {!isLoadingTVChannels && !tvChannelsError && tvChannels?.length === 0 ? (
            <Alert severity="info">No TV channels are available to map yet.</Alert>
          ) : null}

          {!isLoadingTVChannels && !tvChannelsError && (tvChannels?.length || 0) > 0 ? (
            <Stack spacing={2}>
              <Alert severity="info" role="status">
                {selectedMappedChannel
                  ? `Selected TV channel: ${selectedMappedChannel.name}`
                  : 'Select one TV channel before confirming the mapping.'}
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
                            p: 2,
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

      {/* String Mapping Dialog */}
      <Dialog
        open={openStringMappingDialog}
        onClose={() => setOpenStringMappingDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add String Mapping</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Search Pattern"
            fullWidth
            value={stringMappingFormData.search_pattern}
            onChange={(e) => setStringMappingFormData({
              ...stringMappingFormData,
              search_pattern: e.target.value
            })}
            sx={{ mb: 2 }}
            placeholder="e.g., ESPN, CNN, etc."
          />
          <FormControlLabel
            control={
              <Switch
                checked={stringMappingFormData.is_exclusion}
                onChange={(e) => setStringMappingFormData({
                  ...stringMappingFormData,
                  is_exclusion: e.target.checked
                })}
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
          <Button
            onClick={handleAddStringMapping}
            variant="contained"
            color="primary"
            disabled={!stringMappingFormData.search_pattern.trim()}
          >
            Add Mapping
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create TV Channel Dialog */}
      <Dialog open={openCreateTVDialog} onClose={() => setOpenCreateTVDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create TV Channel from EPG</DialogTitle>
        <DialogContent>
          <Box my={2}>
            <TextField
              name="name"
              label="Channel Name"
              fullWidth
              value={createTVForm.name}
              onChange={e => setCreateTVForm(f => ({ ...f, name: e.target.value }))}
              required
              margin="dense"
            />
            <TextField
              name="logo_url"
              label="Logo URL"
              fullWidth
              value={createTVForm.logo_url}
              onChange={e => setCreateTVForm(f => ({ ...f, logo_url: e.target.value }))}
              margin="dense"
            />
            <TextField
              name="description"
              label="Description"
              fullWidth
              value={createTVForm.description}
              onChange={e => setCreateTVForm(f => ({ ...f, description: e.target.value }))}
              margin="dense"
              multiline
              rows={2}
            />
            <TextField
              name="category"
              label="Category"
              fullWidth
              value={createTVForm.category}
              onChange={e => setCreateTVForm(f => ({ ...f, category: e.target.value }))}
              margin="dense"
            />
            <TextField
              name="country"
              label="Country"
              fullWidth
              value={createTVForm.country}
              onChange={e => setCreateTVForm(f => ({ ...f, country: e.target.value }))}
              margin="dense"
            />
            <TextField
              name="language"
              label="Language"
              fullWidth
              value={createTVForm.language}
              onChange={e => setCreateTVForm(f => ({ ...f, language: e.target.value }))}
              margin="dense"
            />
            <TextField
              name="epg_id"
              label="EPG ID"
              fullWidth
              value={channel.channel_xml_id}
              InputProps={{ readOnly: true }}
              margin="dense"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateTVDialog(false)} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleCreateTVChannel}
            color="primary"
            variant="contained"
            disabled={!createTVForm.name || isCreatingTVChannel}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        onClose={closeSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={closeSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EPGChannelDetail;
