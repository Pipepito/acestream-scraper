import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
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
} from '@mui/material';
import {
  Add as AddIcon,
  ArrowBack as BackIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Link as LinkIcon,
  PlayArrow as PlayIcon,
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

  const { data: acestreamCandidates, isLoading: isLoadingAcestreamCandidates } = useAcestreamChannels(
    searchTerm ? { search: searchTerm } : {},
    { staleTime: 1000 * 60 }
  );

  const acestreamCandidateItems = acestreamCandidates?.items || [];

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
    } catch (error) {
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
    } catch (error) {
      console.error('Error removing acestream:', error);
    }
  };

  const handleAssociateSelected = async () => {
    for (const aceStreamId of selectedAcestreams) {
      try {
        await associateAcestreamMutation.mutateAsync({
          tvChannelId: channelId,
          aceStreamId,
        });
      } catch (error) {
        console.error('Error associating acestream:', error);
      }
    }

    setOpenAssociateDialog(false);
    setSelectedAcestreams([]);
  };

  if (isLoading) {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
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
                    <IconButton edge="end" color="primary" aria-label={`Play acestream ${acestream.name}`}>
                      <PlayIcon />
                    </IconButton>
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

      {channel.epg_id ? (
        <ContentSection
          title="EPG Schedule"
          description="Review the resolved guide feed for this TV channel without leaving the detail route."
        >
          <EPGProgramsTable epgId={channel.epg_id} epgSourceId={channel.epg_source_id} />
        </ContentSection>
      ) : null}

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
            <LinearProgress sx={{ mb: 2 }} />
          ) : null}
          <List sx={{ maxHeight: 350, overflow: 'auto' }}>
            {acestreamCandidateItems.length === 0 ? (
              <ListItem>
                <ListItemText primary="No Acestream channels found." />
              </ListItem>
            ) : (
              acestreamCandidateItems.map((acestream) => (
                <ListItem
                  key={acestream.id}
                  divider
                  secondaryAction={
                    <IconButton
                      edge="end"
                      color="primary"
                      aria-label={`Associate acestream ${acestream.name}`}
                      onClick={async () => {
                        try {
                          await associateAcestreamMutation.mutateAsync({
                            tvChannelId: channelId,
                            aceStreamId: acestream.id,
                          });
                          setOpenAssociateDialog(false);
                        } catch (error) {
                          console.error('Error associating acestream:', error);
                        }
                      }}
                    >
                      <AddIcon />
                    </IconButton>
                  }
                >
                  <ListItemText
                    primary={acestream.name}
                    secondary={`ID: ${acestream.id} | Group: ${acestream.group || 'None'}`}
                    onClick={() => {
                      setSelectedAcestreams((prev) =>
                        prev.includes(acestream.id) ? prev.filter((item) => item !== acestream.id) : [...prev, acestream.id]
                      );
                    }}
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
