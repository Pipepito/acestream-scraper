import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add as AddIcon, ArrowBack as BackIcon, Delete as DeleteIcon, Edit as EditIcon, ExpandLess, ExpandMore } from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import BatchAcestreamAssignment from '../components/BatchAcestreamAssignment';
import ScheduleView from '../components/epg/ScheduleView';
import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import { useConfirm } from '../components/ConfirmDialog';
import { useAcestreamChannels } from '../hooks/useChannels';
import { useResolveEPGChannel } from '../hooks/useEPG';
import {
  useAssociateAcestream,
  useRemoveAcestreamAssociation,
  useTVChannel,
  useTVChannelAcestreams,
  useUpdateTVChannel,
} from '../hooks/useTVChannels';

interface EditFormData {
  name: string;
  logo_url: string;
  description: string;
  category: string;
  country: string;
  language: string;
  website: string;
  epg_id: string;
  channel_number: number | '';
  is_active: boolean;
  is_favorite: boolean;
}

const TVChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const channelId = id ? parseInt(id, 10) : 0;
  const { confirm, dialog: confirmDialog } = useConfirm();

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
  const [moreFieldsOpen, setMoreFieldsOpen] = useState(false);
  const [notice, setNotice] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);
  const [editFormData, setEditFormData] = useState<EditFormData>({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    website: '',
    epg_id: '',
    channel_number: '',
    is_active: true,
    is_favorite: false,
  });

  const { data: acestreamCandidates, isLoading: isLoadingAcestreamCandidates, isError: isErrorLoadingAcestreamCandidates } = useAcestreamChannels(
    searchTerm ? { search: searchTerm } : {},
    { staleTime: 1000 * 60, enabled: openAssociateDialog }
  );
  const { data: epgChannel, isLoading: isResolvingEpg, isError: isEpgResolveError } = useResolveEPGChannel(
    channel?.epg_source_id ?? undefined,
    channel?.epg_id ?? undefined
  );

  const acestreamCandidateItems = acestreamCandidates?.items || [];

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
      channel_number: channel.channel_number || '',
      is_active: channel.is_active,
      is_favorite: channel.is_favorite,
    });
    setMoreFieldsOpen(Boolean(channel.description || channel.logo_url || channel.website || channel.language || channel.country));
    setIsEditing(true);
  };

  const handleEditFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setEditFormData((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
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
    } catch {
      setNotice({ message: 'Failed to update TV channel.', severity: 'error' });
    }
  };

  const handleRemoveAcestream = async (aceStreamId: string) => {
    const stream = channel?.acestream_channels.find((item) => item.id === aceStreamId);
    const ok = await confirm({
      title: `Remove ${stream?.name || aceStreamId} from this channel?`,
      body: 'The stream stays in the Acestream inventory; it just stops feeding this TV channel.',
      confirmLabel: 'Remove',
      danger: true,
    });
    if (!ok) return;
    try {
      await removeAcestreamMutation.mutateAsync({ tvChannelId: channelId, aceStreamId });
      setNotice({ message: `Removed acestream ${stream?.name || aceStreamId} successfully.`, severity: 'success' });
    } catch {
      setNotice({ message: 'Failed to remove acestream.', severity: 'error' });
    }
  };

  const handleAssociateSelected = async () => {
    const assignedCount = selectedAcestreams.length;
    for (const aceStreamId of selectedAcestreams) {
      try {
        await associateAcestreamMutation.mutateAsync({ tvChannelId: channelId, aceStreamId });
      } catch {
        setNotice({ message: 'Failed to assign selected acestream sources.', severity: 'error' });
        return;
      }
    }
    setOpenAssociateDialog(false);
    setSelectedAcestreams([]);
    setNotice({ message: `Assigned ${assignedCount} acestream source${assignedCount === 1 ? '' : 's'} successfully.`, severity: 'success' });
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
        <Button startIcon={<BackIcon />} onClick={() => navigate('/tv-channels')} aria-label="Back to TV channels">
          Back to TV Channels
        </Button>
      </Box>
    );
  }

  const streamCount = channel.acestream_channels.length;
  const subtitle = [channel.category, channel.channel_number ? `Channel ${channel.channel_number}` : null].filter(Boolean).join(' · ') || undefined;

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title={channel.name}
        subtitle={subtitle}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" startIcon={<BackIcon />} onClick={() => navigate('/tv-channels')}>
              Back
            </Button>
            {!isEditing ? (
              <Button variant="contained" startIcon={<EditIcon />} onClick={handleEdit}>
                Edit
              </Button>
            ) : null}
          </Stack>
        }
      />

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap role="group" aria-label="Channel summary" sx={{ mb: 2 }}>
        <Chip label={channel.is_active ? 'Active' : 'Hidden'} color={channel.is_active ? 'success' : 'default'} size="small" variant="outlined" />
        {channel.is_favorite ? <Chip label="Favorite" color="warning" size="small" variant="outlined" /> : null}
        <Chip label={`${streamCount} stream${streamCount === 1 ? '' : 's'}`} size="small" variant="outlined" color={streamCount === 0 ? 'warning' : 'default'} />
        <Chip label={channel.epg_id ? `EPG: ${channel.epg_id}` : 'EPG: not mapped'} size="small" variant="outlined" color={channel.epg_id ? 'default' : 'warning'} sx={{ fontFamily: channel.epg_id ? 'monospace' : undefined }} />
        {epgChannel ? (
          <Chip
            component={RouterLink}
            to={`/epg/channels/${epgChannel.id}`}
            clickable
            label={`Guide channel: ${epgChannel.name}`}
            size="small"
            variant="outlined"
            color="primary"
          />
        ) : null}
      </Stack>

      {notice ? (
        <Alert severity={notice.severity} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {notice.message}
        </Alert>
      ) : null}

      {isEditing ? (
        <ContentSection title="Edit channel">
          <Stack spacing={2} component="form" onSubmit={(event) => { event.preventDefault(); void handleSaveEdit(); }}>
            <TextField name="name" label="Name" value={editFormData.name} onChange={handleEditFormChange} required fullWidth />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField name="category" label="Category" value={editFormData.category} onChange={handleEditFormChange} fullWidth />
              <TextField name="channel_number" label="Channel number" type="number" value={editFormData.channel_number} onChange={handleEditFormChange} sx={{ minWidth: 160 }} />
            </Stack>
            <TextField
              name="epg_id"
              label="EPG ID"
              value={editFormData.epg_id}
              onChange={handleEditFormChange}
              fullWidth
              helperText="The guide channel's XML id. Set it to show the schedule below."
              InputProps={{ sx: { fontFamily: 'monospace' } }}
            />
            <Stack direction="row" spacing={2}>
              <FormControlLabel control={<Checkbox name="is_active" checked={editFormData.is_active} onChange={handleEditFormChange} />} label="Active" />
              <FormControlLabel control={<Checkbox name="is_favorite" checked={editFormData.is_favorite} onChange={handleEditFormChange} />} label="Favorite" />
            </Stack>
            <Button
              onClick={() => setMoreFieldsOpen((value) => !value)}
              aria-expanded={moreFieldsOpen}
              endIcon={moreFieldsOpen ? <ExpandLess /> : <ExpandMore />}
              sx={{ alignSelf: 'flex-start' }}
            >
              {moreFieldsOpen ? 'Fewer fields' : 'More fields'}
            </Button>
            <Collapse in={moreFieldsOpen} unmountOnExit>
              <Stack spacing={2}>
                <TextField name="description" label="Description" value={editFormData.description} onChange={handleEditFormChange} fullWidth multiline rows={2} />
                <TextField name="logo_url" label="Logo URL" value={editFormData.logo_url} onChange={handleEditFormChange} fullWidth />
                <TextField name="website" label="Website" value={editFormData.website} onChange={handleEditFormChange} fullWidth />
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField name="language" label="Language" value={editFormData.language} onChange={handleEditFormChange} fullWidth />
                  <TextField name="country" label="Country" value={editFormData.country} onChange={handleEditFormChange} fullWidth />
                </Stack>
              </Stack>
            </Collapse>
            <Stack direction="row" spacing={1}>
              <Button type="submit" variant="contained">
                Save
              </Button>
              <Button onClick={() => setIsEditing(false)}>Cancel</Button>
            </Stack>
          </Stack>
        </ContentSection>
      ) : null}

      <ContentSection
        title="Streams"
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setOpenAssociateDialog(true)}>
              Add stream
            </Button>
            <Button variant="outlined" size="small" onClick={() => setOpenBatchAssignDialog(true)}>
              Add many
            </Button>
          </Stack>
        }
      >
        {streamCount === 0 ? (
          <Alert severity="info">No streams yet. Add one so this channel can play.</Alert>
        ) : (
          <List sx={{ p: 0 }}>
            {channel.acestream_channels.map((acestream) => (
              <ListItem
                key={acestream.id}
                divider
                sx={{ alignItems: 'flex-start', pr: 7 }}
                secondaryAction={
                  <Box role="group" aria-label={`Acestream actions for ${acestream.name}`}>
                    <Tooltip title="Remove from this channel">
                      <IconButton edge="end" color="error" aria-label={`Remove acestream ${acestream.name}`} onClick={() => handleRemoveAcestream(acestream.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <ListItemText
                  primary={acestream.name}
                  primaryTypographyProps={{ fontWeight: 600 }}
                  secondary={
                    <Stack component="span" direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 0.5 }}>
                      {acestream.is_online !== undefined && acestream.is_online !== null ? (
                        <Chip component="span" size="small" variant="outlined" label={acestream.is_online ? 'Online' : 'Offline'} color={acestream.is_online ? 'success' : 'error'} />
                      ) : null}
                      {acestream.group ? <Chip component="span" size="small" variant="outlined" label={acestream.group} /> : null}
                      <Typography component="span" variant="body2" sx={{ fontFamily: 'monospace', alignSelf: 'center', overflowWrap: 'anywhere' }}>
                        {acestream.id}
                      </Typography>
                    </Stack>
                  }
                  secondaryTypographyProps={{ component: 'div' }}
                />
              </ListItem>
            ))}
          </List>
        )}
      </ContentSection>

      <ContentSection title="Schedule">
        {!channel.epg_id ? (
          <Alert severity="info">No EPG ID yet. Edit the channel and set one to see the schedule here.</Alert>
        ) : isResolvingEpg ? (
          <Box role="status" aria-live="polite">
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2">Finding the guide channel…</Typography>
          </Box>
        ) : epgChannel ? (
          <ScheduleView epgChannelId={epgChannel.id} />
        ) : (
          <Alert severity="warning">
            {isEpgResolveError
              ? 'Unable to look up the guide channel right now.'
              : `No guide channel with id “${channel.epg_id}” was found in the EPG sources. Check the ID or refresh the sources.`}
          </Alert>
        )}
      </ContentSection>

      <Dialog open={openAssociateDialog} onClose={() => setOpenAssociateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add a stream</DialogTitle>
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
                        setSelectedAcestreams((prev) => (checked ? [...prev, acestream.id] : prev.filter((item) => item !== acestream.id)));
                      }}
                    />
                  }
                >
                  <ListItemText primary={acestream.name} secondary={`ID: ${acestream.id} | Group: ${acestream.group || 'None'}`} />
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

      {confirmDialog}
    </Box>
  );
};

export default TVChannelDetail;
