import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  alpha,
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Stack,
  Switch,
  TextField,
  Typography,
  FormControlLabel,
  useTheme,
} from '@mui/material';
import {
  Add as AddIcon,
  ArrowBack as BackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Link as LinkIcon,
} from '@mui/icons-material';

import BatchAcestreamAssignment from '../components/BatchAcestreamAssignment';
import EPGProgramsTable from '../components/EPGProgramsTable';
import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import { useAcestreamChannels } from '../hooks/useChannels';
import {
  useAssociateAcestream,
  useRemoveAcestreamAssociation,
  useTVChannel,
  useTVChannelAcestreams,
  useUpdateTVChannel,
} from '../hooks/useTVChannels';

const TVChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const channelId = id ? parseInt(id, 10) : 0;

  const { data: channel, isLoading, isError } = useTVChannel(channelId);
  useTVChannelAcestreams(channelId);

  const associateAcestreamMutation = useAssociateAcestream();
  const removeAcestreamMutation = useRemoveAcestreamAssociation();
  const updateChannelMutation = useUpdateTVChannel();

  const [openAssociateDialog, setOpenAssociateDialog] = useState(false);
  const [openBatchAssignDialog, setOpenBatchAssignDialog] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAcestreams, setSelectedAcestreams] = useState<string[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [notice, setNotice] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);
  const [editFormData, setEditFormData] = useState({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    website: '',
    epg_id: '',
    channel_number: 0,
    is_active: true,
    is_favorite: false,
  });

  const { data: acestreamCandidates, isLoading: isLoadingAcestreamCandidates, isError: isErrorLoadingAcestreamCandidates } = useAcestreamChannels(
    searchTerm ? { search: searchTerm } : {},
    { staleTime: 1000 * 60, enabled: openAssociateDialog }
  );

  const acestreamCandidateItems = acestreamCandidates?.items || [];
  const linkedAcestreamCount = channel?.acestream_channels.length || 0;
  const hasEpgLink = Boolean(channel?.epg_id);
  const identitySummary = channel
    ? `${channel.name} is ${channel.is_active ? 'active' : 'inactive'}, ${channel.is_favorite ? 'marked favorite' : 'not marked favorite'}, and ${linkedAcestreamCount === 0 ? 'still waiting for source coverage' : hasEpgLink ? 'ready for playback and guide review' : 'ready for playback but still missing guide review'}.`
    : '';
  const relationshipStatus = linkedAcestreamCount === 0
    ? 'Playback coverage incomplete'
    : hasEpgLink
      ? 'Operational relationship in place'
      : 'Guide linkage still missing';
  const relationshipSupport = linkedAcestreamCount === 0
    ? 'No linked acestream sources are available yet, so playback coverage is still incomplete for this channel.'
    : hasEpgLink
      ? 'Linked source coverage and guide linkage are both present, so this channel is ready for routine review or cleanup.'
      : 'Playback coverage is in place, but guide linkage is still missing for downstream schedule review.';
  const nextStepLabel = linkedAcestreamCount === 0
    ? 'Link at least one acestream source before you treat this channel as ready for playback or guide follow-up.'
    : hasEpgLink
      ? 'Keep linked sources and guide data aligned, and remove stale relationships only when cleanup is needed.'
      : 'Add the correct EPG ID so downstream schedule review can start from this same detail page.';

  const handleGoBack = () => {
    navigate('/tv-channels');
  };

  const handleEdit = () => {
    if (!channel) return;

    setEditFormData({
      name: channel.name,
      logo_url: channel.logo_url || '',
      description: channel.description || '',
      category: channel.category || '',
      country: channel.country || '',
      language: channel.language || '',
      website: channel.website || '',
      epg_id: channel.epg_id || '',
      channel_number: channel.channel_number || 0,
      is_active: channel.is_active,
      is_favorite: channel.is_favorite,
    });
    setIsEditing(true);
  };

  const handleEditFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setEditFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSaveEdit = async () => {
    try {
      await updateChannelMutation.mutateAsync({
        id: channelId,
        updates: {
          name: editFormData.name,
          logo_url: editFormData.logo_url,
          description: editFormData.description,
          category: editFormData.category,
          country: editFormData.country,
          language: editFormData.language,
          website: editFormData.website,
          epg_id: editFormData.epg_id,
          channel_number: editFormData.channel_number ? Number(editFormData.channel_number) : undefined,
          is_active: editFormData.is_active,
          is_favorite: editFormData.is_favorite,
        },
      });
      setIsEditing(false);
      setNotice({ message: 'TV channel updated successfully.', severity: 'success' });
    } catch (error) {
      setNotice({ message: 'Failed to update TV channel.', severity: 'error' });
      console.error('Error updating TV channel:', error);
    }
  };

  const handleRemoveAcestream = async (aceStreamId: string) => {
    if (!window.confirm('Are you sure you want to remove this acestream?')) return;

    try {
      await removeAcestreamMutation.mutateAsync({
        tvChannelId: channelId,
        aceStreamId,
      });
      const removedAcestream = channel?.acestream_channels.find((item) => item.channel_id === aceStreamId);
      setNotice({
        message: `Removed acestream ${removedAcestream?.name || aceStreamId} successfully.`,
        severity: 'success',
      });
    } catch (error) {
      setNotice({ message: 'Failed to remove acestream.', severity: 'error' });
      console.error('Error removing acestream:', error);
    }
  };

  const handleAssociateSelected = async () => {
    const assignedCount = selectedAcestreams.length;

    for (const aceStreamId of selectedAcestreams) {
      try {
        await associateAcestreamMutation.mutateAsync({
          tvChannelId: channelId,
          aceStreamId,
        });
      } catch (error) {
        setNotice({ message: 'Failed to assign selected acestream sources.', severity: 'error' });
        console.error('Error associating acestream:', error);
        return;
      }
    }

    setOpenAssociateDialog(false);
    setSelectedAcestreams([]);
    setNotice({
      message: `Assigned ${assignedCount} acestream source${assignedCount === 1 ? '' : 's'} successfully.`,
      severity: 'success',
    });
  };

  if (isLoading) {
    return (
      <Box sx={{ width: '100%', p: 3 }} role="status" aria-live="polite">
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Loading TV channel details...
        </Typography>
      </Box>
    );
  }

  if (isError || !channel) {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading TV channel details.
        </Alert>
        <Button startIcon={<BackIcon />} onClick={handleGoBack} aria-label="Back to TV channels">
          Back to TV Channels
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title={channel.name}
        subtitle="Review channel identity, manage linked Acestream sources, and confirm guide coverage from one operational detail route."
        actions={
          <>
            <Button variant="outlined" startIcon={<BackIcon />} onClick={handleGoBack} aria-label="Back to TV channels">
              Back to TV Channels
            </Button>
            {isEditing ? (
              <>
                <Button variant="contained" onClick={handleSaveEdit}>
                  Save
                </Button>
                <Button variant="outlined" color="inherit" onClick={() => setIsEditing(false)}>
                  Cancel
                </Button>
              </>
            ) : (
              <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
                Edit
              </Button>
            )}
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
          <Box sx={{ minWidth: 0, maxWidth: 760 }}>
            <Typography variant="statusMeta" sx={{ color: theme.appTokens.hero.accent, mb: 1 }}>
              Relationship summary
            </Typography>
            <Typography variant="h4" sx={{ letterSpacing: '-0.03em', mb: 1 }}>
              {identitySummary}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {relationshipSupport}
            </Typography>
          </Box>
          <Stack spacing={1} sx={{ minWidth: { xs: '100%', sm: 320 } }}>
            <Box
              sx={{
                p: 1.5,
                borderRadius: 2,
                bgcolor: alpha(theme.appTokens.shell.accent, 0.08),
                border: `1px solid ${alpha(theme.appTokens.shell.accent, 0.18)}`,
              }}
            >
              <Typography variant="statusMeta" sx={{ color: 'text.secondary', mb: 0.5 }}>
                Relationship status
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                {relationshipStatus}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {linkedAcestreamCount} linked acestream source{linkedAcestreamCount === 1 ? '' : 's'} {hasEpgLink ? 'with guide linkage in place.' : 'and no guide linkage yet.'}
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
          </Stack>
        </Box>
      </Box>

      {notice ? (
        <Alert severity={notice.severity} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {notice.message}
        </Alert>
      ) : null}

      <ContentSection
        title="Channel Summary"
        description="Confirm the TV channel identity, metadata, and operational state before changing assignments."
      >
        <Stack spacing={2}>
          {!isEditing && channel.logo_url ? (
            <Box
              component="img"
              src={channel.logo_url}
              alt={`${channel.name} logo`}
              sx={{ width: 96, height: 96, objectFit: 'contain', borderRadius: 2, border: 1, borderColor: 'divider', p: 1 }}
            />
          ) : null}

          {isEditing ? (
            <Box sx={{ display: 'grid', gap: 2, gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' } }}>
              <TextField label="Name" name="name" value={editFormData.name} onChange={handleEditFormChange} fullWidth required />
              <TextField label="Logo URL" name="logo_url" value={editFormData.logo_url} onChange={handleEditFormChange} fullWidth />
              <TextField label="Category" name="category" value={editFormData.category} onChange={handleEditFormChange} fullWidth />
              <TextField label="Language" name="language" value={editFormData.language} onChange={handleEditFormChange} fullWidth />
              <TextField label="Country" name="country" value={editFormData.country} onChange={handleEditFormChange} fullWidth />
              <TextField label="Website" name="website" value={editFormData.website} onChange={handleEditFormChange} fullWidth />
              <TextField label="EPG ID" name="epg_id" value={editFormData.epg_id} onChange={handleEditFormChange} fullWidth />
              <TextField label="Channel Number" name="channel_number" type="number" value={editFormData.channel_number} onChange={handleEditFormChange} fullWidth />
              <TextField
                label="Description"
                name="description"
                value={editFormData.description}
                onChange={handleEditFormChange}
                fullWidth
                multiline
                rows={3}
                sx={{ gridColumn: { md: '1 / -1' } }}
              />
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', gridColumn: { md: '1 / -1' } }}>
                <FormControlLabel control={<Switch checked={editFormData.is_active} onChange={handleEditFormChange} name="is_active" />} label="Active" />
                <FormControlLabel control={<Switch checked={editFormData.is_favorite} onChange={handleEditFormChange} name="is_favorite" />} label="Favorite" />
              </Box>
            </Box>
          ) : (
            <>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={channel.is_active ? 'Status: Active' : 'Status: Inactive'} color={channel.is_active ? 'success' : 'default'} size="small" />
                <Chip label={channel.is_favorite ? 'Favorite channel' : 'Not marked favorite'} color={channel.is_favorite ? 'primary' : 'default'} size="small" />
                {channel.category ? <Chip label={`Category: ${channel.category}`} size="small" /> : null}
              </Box>
              <Stack spacing={1}>
                {channel.language ? <Typography variant="body2">Language: {channel.language}</Typography> : null}
                {channel.country ? <Typography variant="body2">Country: {channel.country}</Typography> : null}
                {channel.epg_id ? <Typography variant="body2">EPG ID: {channel.epg_id}</Typography> : null}
                {channel.channel_number !== undefined ? <Typography variant="body2">Channel Number: {channel.channel_number}</Typography> : null}
                {channel.description ? <Typography variant="body2">{channel.description}</Typography> : null}
              </Stack>
              {channel.website ? (
                <Button
                  startIcon={<LinkIcon />}
                  variant="text"
                  color="primary"
                  href={channel.website}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Visit Website
                </Button>
              ) : null}
            </>
          )}
        </Stack>
      </ContentSection>

      <ContentSection
        title="Acestream Coverage"
        description="Add or remove linked Acestream sources so playback coverage matches the TV channel you expect users to see."
        actions={
          <>
            <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setOpenAssociateDialog(true)}>
              Add Single
            </Button>
            <Button variant="outlined" size="small" onClick={() => setOpenBatchAssignDialog(true)}>
              Batch Add
            </Button>
          </>
        }
      >
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          <Chip label={`${channel.acestream_channels.length} linked acestream${channel.acestream_channels.length === 1 ? '' : 's'}`} size="small" />
        </Box>

        {channel.acestream_channels.length === 0 ? (
          <Alert severity="info">No acestream channels are associated with this TV channel yet.</Alert>
        ) : (
          <List sx={{ p: 0 }}>
            {channel.acestream_channels.map((acestream) => (
              <ListItem
                key={acestream.channel_id}
                divider
                secondaryAction={
                  <Box role="group" aria-label={`Acestream actions for ${acestream.name}`} sx={{ display: 'flex', gap: 1 }}>
                    <IconButton
                      edge="end"
                      color="error"
                      aria-label={`Remove acestream ${acestream.name}`}
                      onClick={() => handleRemoveAcestream(acestream.channel_id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                }
              >
                <ListItemText primary={acestream.name} />
                <Box sx={{ display: 'inline-flex', gap: 1, flexWrap: 'wrap', mt: 0.75 }}>
                  <Chip size="small" label={`ID: ${acestream.channel_id}`} />
                  <Chip size="small" label={`Group: ${acestream.group || 'None'}`} />
                  {acestream.is_online !== undefined ? (
                    <Chip size="small" label={acestream.is_online ? 'Online' : 'Offline'} color={acestream.is_online ? 'success' : 'default'} />
                  ) : null}
                </Box>
              </ListItem>
            ))}
          </List>
        )}
      </ContentSection>

      <ContentSection
        title="EPG Schedule"
        description="Review the resolved guide feed for this TV channel without leaving the detail route."
      >
        {channel.epg_id ? (
          <EPGProgramsTable epgId={channel.epg_id} epgSourceId={channel.epg_source_id} />
        ) : (
          <Alert severity="info">
            Guide linkage is still incomplete, so schedule review will appear here after you add the correct EPG ID.
          </Alert>
        )}
      </ContentSection>

      <Dialog open={openAssociateDialog} onClose={() => setOpenAssociateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Associate Acestream Channel</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="Search by name, group, or ID"
            fullWidth
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Type to search..."
            variant="outlined"
            sx={{ mb: 2 }}
          />
          {isLoadingAcestreamCandidates ? (
            <Box sx={{ mb: 2 }} role="status" aria-live="polite">
              <LinearProgress sx={{ mb: 1 }} />
              <Typography variant="body2">Loading Acestream candidates...</Typography>
            </Box>
          ) : null}
          {isErrorLoadingAcestreamCandidates ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Unable to load Acestream candidates. Try searching again in a moment.
            </Alert>
          ) : null}
          <Alert severity="info" sx={{ mb: 2 }} role="status">
            {selectedAcestreams.length === 0
              ? 'Select one or more Acestream sources before assigning them.'
              : `${selectedAcestreams.length} acestream selected for assignment.`}
          </Alert>
          <List sx={{ maxHeight: 350, overflow: 'auto' }}>
            {isErrorLoadingAcestreamCandidates ? null : acestreamCandidateItems.length === 0 ? (
              <ListItem>
                <ListItemText primary="No Acestream channels found." />
              </ListItem>
            ) : (
              acestreamCandidateItems.map((acestream) => (
                <ListItem
                  key={acestream.id}
                  divider
                  secondaryAction={
                    <Checkbox
                      edge="end"
                      color="primary"
                      inputProps={{ 'aria-label': `Select acestream ${acestream.name}` }}
                      checked={selectedAcestreams.includes(acestream.id)}
                      onChange={(_event, checked) => {
                        setSelectedAcestreams((prev) =>
                          checked ? [...prev, acestream.id] : prev.filter((item) => item !== acestream.id)
                        );
                      }}
                    />
                  }
                >
                  <ListItemText
                    primary={acestream.name}
                    secondary={`ID: ${acestream.id} | Group: ${acestream.group || 'None'}`}
                  />
                </ListItem>
              ))
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAssociateDialog(false)} color="inherit">
            Cancel
          </Button>
          <Button onClick={handleAssociateSelected} color="primary" variant="contained" disabled={selectedAcestreams.length === 0}>
            Assign Selected
          </Button>
        </DialogActions>
      </Dialog>

      <BatchAcestreamAssignment
        open={openBatchAssignDialog}
        onClose={() => setOpenBatchAssignDialog(false)}
        tvChannelId={channelId}
        tvChannelName={channel.name}
      />
    </Box>
  );
};

export default TVChannelDetail;
