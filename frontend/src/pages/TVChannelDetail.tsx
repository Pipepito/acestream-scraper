import {
Add as AddIcon,
ArrowDownward,
ArrowUpward,
ArrowBack as BackIcon,
Delete as DeleteIcon,
DragIndicator,
Edit as EditIcon,
ExpandLess,
ExpandMore,
Save as SaveIcon,
} from '@mui/icons-material';
import PlayArrowRounded from '@mui/icons-material/PlayArrowRounded';
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
import React,{ useRef,useState } from 'react';
import { Link as RouterLink,useNavigate,useParams } from 'react-router-dom';
import BatchAcestreamAssignment from '../components/BatchAcestreamAssignment';
import { useConfirm } from '../components/ConfirmDialog';
import ScheduleView from '../components/epg/ScheduleView';
import ContentSection from '../components/layout/ContentSection';
import PageHeader from '../components/layout/PageHeader';
import ChannelPlayerDialog from '../components/player/ChannelPlayerDialog';
import { useUnsavedChanges } from '../components/UnsavedChanges';
import { useAcestreamChannels } from '../hooks/useChannels';
import { useResolveEPGChannel } from '../hooks/useEPG';
import { resolveSnackbarMessage,type SnackbarMessage } from '../hooks/useSnackbar';
import GuideSourceField, { guideSourcePayload } from '../components/GuideSourceField';
import {
useAssociateAcestream,
useRemoveAcestreamAssociation,
useReorderTVChannelAcestreams,
useTVChannel,
useTVChannelAcestreams,
useUpdateTVChannel,
} from '../hooks/useTVChannels';
import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import { AcestreamChannel } from '../types/channelTypes';
import { getErrorMessage } from '../utils/errorUtils';

interface EditFormData {
  name: string;
  logo_url: string;
  description: string;
  category: string;
  country: string;
  language: string;
  website: string;
  epg_id: string;
  epg_source_id: number | '';
  channel_number: number | '';
  is_active: boolean;
  is_favorite: boolean;
}

interface StreamOrderDraft {
  channelId: number;
  streams: AcestreamChannel[];
  expectedOrder: string[];
}

const TVChannelDetail: React.FC = () => {
  const tUi = useUiText();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const channelId = id ? parseInt(id, 10) : 0;
  const { confirm, dialog: confirmDialog } = useConfirm();

  const { data: channel, isLoading, isError } = useTVChannel(channelId);
  useTVChannelAcestreams(channelId);

  const associateAcestreamMutation = useAssociateAcestream();
  const removeAcestreamMutation = useRemoveAcestreamAssociation();
  const updateChannelMutation = useUpdateTVChannel();
  const reorderStreamsMutation = useReorderTVChannelAcestreams();

  const [orderDraft, setOrderDraft] = useState<StreamOrderDraft | null>(null);
  const draft = orderDraft?.channelId === channelId ? orderDraft : null;
  const orderedStreams = draft?.streams ?? channel?.acestream_channels ?? [];
  const isOrderModified = draft !== null && orderedStreams.some((stream, index) => stream.id !== draft.expectedOrder[index]);
  const [isSavingOrder, setIsSavingOrder] = useState(false);
  const savingOrder = useRef(false);
  const savingEdit = useRef(false);
  const assigning = useRef(false);
  const [isAssigning, setIsAssigning] = useState(false);
  const removing = useRef(new Set<string>());
  const editBaseline = useRef('');
  const draggedStreamId = useRef<string | null>(null);
  const [dragOverStreamId, setDragOverStreamId] = useState<string | null>(null);

  const moveStream = (id: string, targetId: string) => {
    if (isSavingOrder || id === targetId) return;
    const from = orderedStreams.findIndex((stream) => stream.id === id);
    const to = orderedStreams.findIndex((stream) => stream.id === targetId);
    if (from < 0 || to < 0) return;
    const next = [...orderedStreams];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    setOrderDraft({
      channelId, streams: next,
      expectedOrder: draft?.expectedOrder ?? orderedStreams.map((stream) => stream.id),
    });
  };

  const moveStreamStep = (index: number, direction: 'up' | 'down') => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= orderedStreams.length) return;
    moveStream(orderedStreams[index].id, orderedStreams[targetIndex].id);
  };

  const handleSaveOrder = async () => {
    if (!channel || !draft || orderedStreams.length < 2 || !isOrderModified || savingOrder.current) return;
    savingOrder.current = true; setIsSavingOrder(true);
    try {
      await reorderStreamsMutation.mutateAsync({
        tvChannelId: channelId,
        streamIds: orderedStreams.map((s) => s.id),
        expectedOrder: draft.expectedOrder,
      });
      setOrderDraft(null);
      setNotice({ message: () => uiText("Stream preference order saved successfully."), severity: 'success' });
    } catch (err) {
      setNotice({ message: () => getErrorMessage(err), severity: 'error' });
    } finally {
      savingOrder.current = false; setIsSavingOrder(false);
    }
  };

  const [openAssociateDialog, setOpenAssociateDialog] = useState(false);
  const [openBatchAssignDialog, setOpenBatchAssignDialog] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAcestreams, setSelectedAcestreams] = useState<string[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [moreFieldsOpen, setMoreFieldsOpen] = useState(false);
  const [notice, setNotice] = useState<{ message: SnackbarMessage; severity: 'success' | 'error' } | null>(null);
  const [playerTarget, setPlayerTarget] = useState<{ contentId: string; title: string } | null>(null);
  const [editFormData, setEditFormData] = useState<EditFormData>({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    website: '',
    epg_id: '',
    epg_source_id: '',
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
    const fields: EditFormData = {
      name: channel.name,
      logo_url: channel.logo_url || '',
      description: channel.description || '',
      category: channel.category || '',
      country: channel.country || '',
      language: channel.language || '',
      website: channel.website || '',
      epg_id: channel.epg_id || '',
      epg_source_id: channel.epg_source_id ?? '',
      channel_number: channel.channel_number ?? '',
      is_active: channel.is_active,
      is_favorite: channel.is_favorite,
    };
    editBaseline.current = JSON.stringify(fields);
    setEditFormData(fields);
    setMoreFieldsOpen(Boolean(channel.description || channel.logo_url || channel.website || channel.language || channel.country));
    setIsEditing(true);
  };

  const handleEditFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setEditFormData((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
  };

  const editDirty = isEditing && JSON.stringify(editFormData) !== editBaseline.current;
  useUnsavedChanges(editDirty || isOrderModified || selectedAcestreams.length > 0, isSavingOrder || updateChannelMutation.isPending || isAssigning);
  const cancelEdit = async () => {
    if (savingEdit.current) return;
    if (editDirty && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    setIsEditing(false);
  };
  const handleSaveEdit = async () => {
    if (savingEdit.current) return;
    const number = editFormData.channel_number === '' ? null : Number(editFormData.channel_number);
    if (number !== null && (!Number.isSafeInteger(number) || number < 0)) {
      setNotice({ message: () => tUi('Use a whole number of 0 or more.'), severity: 'error' }); return;
    }
    savingEdit.current = true;
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
          epg_source_id: guideSourcePayload(editFormData.epg_source_id),
          channel_number: number,
          is_active: editFormData.is_active,
          is_favorite: editFormData.is_favorite,
        },
      });
      setIsEditing(false);
      setNotice({ message: () => uiText("TV channel updated successfully."), severity: 'success' });
    } catch (error) {
      setNotice({ message: () => getErrorMessage(error), severity: 'error' });
    } finally { savingEdit.current = false; }
  };

  const handleRemoveAcestream = async (aceStreamId: string) => {
    if (removing.current.has(aceStreamId)) return;
    const stream = channel?.acestream_channels.find((item) => item.id === aceStreamId);
    const ok = await confirm(() => ({
      title: uiText("Remove {{name}} from this channel?", { name: stream?.name || aceStreamId }),
      body: uiText("The stream stays in the Acestream inventory; it just stops feeding this TV channel."),
      confirmLabel: uiText("Remove"),
      danger: true,
    }));
    if (!ok || removing.current.has(aceStreamId)) return;
    removing.current.add(aceStreamId);
    try {
      await removeAcestreamMutation.mutateAsync({ tvChannelId: channelId, aceStreamId });
      setNotice({ message: () => uiText('Removed {{name}} from this channel.', { name: stream?.name || aceStreamId }), severity: 'success' });
    } catch {
      setNotice({ message: () => uiText("Failed to remove acestream."), severity: 'error' });
    } finally { removing.current.delete(aceStreamId); }
  };

  const closeAssociation = async () => {
    if (assigning.current) return;
    if (selectedAcestreams.length && !await confirm(() => ({ title: tUi('Discard unsaved changes?'), body: tUi('Your changes have not been saved. Stay to continue editing, or discard them and leave.'), confirmLabel: tUi('Discard changes'), danger: true }))) return;
    setSelectedAcestreams([]); setOpenAssociateDialog(false);
  };
  const handleAssociateSelected = async () => {
    if (assigning.current || !selectedAcestreams.length) return;
    assigning.current = true; setIsAssigning(true);
    const selected = [...selectedAcestreams];
    try {
      for (const aceStreamId of selected) {
        await associateAcestreamMutation.mutateAsync({ tvChannelId: channelId, aceStreamId });
        setSelectedAcestreams(current => current.filter(id => id !== aceStreamId));
      }
      setOpenAssociateDialog(false);
      setNotice({ message: () => uiText('assignedStreamCount', { count: selected.length }), severity: 'success' });
    } catch (error) {
      setNotice({ message: () => getErrorMessage(error), severity: 'error' });
    } finally { assigning.current = false; setIsAssigning(false); }
  };

  if (isLoading) {
    return (
      <Box sx={{ width: '100%', p: 3 }} role="status" aria-live="polite">
        <LinearProgress />
        <Typography variant="body1" sx={{ mt: 2 }}>
          {tUi("Loading TV channel details...")}</Typography>
      </Box>
    );
  }

  if (isError || !channel) {
    return (
      <Box sx={{ width: '100%', p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {tUi("Error loading TV channel details.")}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/tv-channels')} aria-label={tUi("Back to TV channels")}>
          {tUi("Back to TV Channels")}</Button>
      </Box>
    );
  }

  const streamCount = channel.acestream_channels.length;
  const subtitle = [channel.category, channel.channel_number != null ? tUi('Channel {{number}}', { number: channel.channel_number }) : null].filter(Boolean).join(' · ') || undefined;

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title={channel.name}
        subtitle={subtitle}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
            <Button variant="outlined" startIcon={<BackIcon />} onClick={() => navigate('/tv-channels')}>
              {tUi("Back")}</Button>
            <Button
              variant="contained"
              startIcon={<PlayArrowRounded />}
              disabled={streamCount === 0}
              onClick={() => setPlayerTarget({ contentId: channel.acestream_channels[0].id, title: channel.name })}
            >
              {tUi("Watch channel")}</Button>
            {!isEditing ? (
              <Button variant="outlined" startIcon={<EditIcon />} onClick={handleEdit}>
                {tUi("Edit")}</Button>
            ) : null}
          </Stack>
        }
      />

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap role="group" aria-label={tUi("Channel summary")} sx={{ mb: 2 }}>
        <Chip label={channel.is_active ? tUi("Active") : tUi("Hidden")} color={channel.is_active ? 'success' : 'default'} size="small" variant="outlined" />
        {channel.is_favorite ? <Chip label={tUi("Favorite")} color="warning" size="small" variant="outlined" /> : null}
        <Chip label={tUi('streamCount', { count: streamCount })} size="small" variant="outlined" color={streamCount === 0 ? 'warning' : 'default'} />
        <Chip label={channel.epg_id ? tUi("EPG: {{value0}}", { value0: channel.epg_id }) : tUi("EPG: not mapped")} size="small" variant="outlined" color={channel.epg_id ? 'default' : 'warning'} sx={{ fontFamily: channel.epg_id ? 'monospace' : undefined }} />
        {epgChannel ? (
          <Chip
            component={RouterLink}
            to={`/epg/channels/${epgChannel.id}`}
            clickable
            label={tUi("Guide channel: {{value0}}", { value0: epgChannel.name })}
            size="small"
            variant="outlined"
            color="primary"
          />
        ) : null}
      </Stack>

      {notice ? (
        <Alert severity={notice.severity} sx={{ mb: 2 }} onClose={() => setNotice(null)}>
          {resolveSnackbarMessage(notice.message)}
        </Alert>
      ) : null}

      {isEditing ? (
        <ContentSection title={tUi("Edit channel")}>
          <Box component="form" onSubmit={(event) => { event.preventDefault(); void handleSaveEdit(); }}><Stack component="fieldset" disabled={updateChannelMutation.isPending} spacing={2} sx={{ p: 0, m: 0, border: 0, minWidth: 0 }}>
            <TextField name="name" label={tUi("Name")} value={editFormData.name} onChange={handleEditFormChange} required fullWidth />
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField name="category" label={tUi("Category")} value={editFormData.category} onChange={handleEditFormChange} fullWidth />
              <TextField name="channel_number" label={tUi("Channel number")} type="number" value={editFormData.channel_number} onChange={handleEditFormChange} sx={{ minWidth: 160 }} />
            </Stack>
            <GuideSourceField value={editFormData.epg_source_id} onChange={handleEditFormChange} />
            <TextField
              name="epg_id"
              label={tUi("EPG ID")}
              value={editFormData.epg_id}
              onChange={handleEditFormChange}
              fullWidth
              helperText={tUi("The guide channel's XML id. Set it to show the schedule below.")}
              InputProps={{ sx: { fontFamily: 'monospace' } }}
            />
            <Stack direction="row" spacing={2}>
              <FormControlLabel control={<Checkbox name="is_active" checked={editFormData.is_active} onChange={handleEditFormChange} />} label={tUi("Active")} />
              <FormControlLabel control={<Checkbox name="is_favorite" checked={editFormData.is_favorite} onChange={handleEditFormChange} />} label={tUi("Favorite")} />
            </Stack>
            <Button
              onClick={() => setMoreFieldsOpen((value) => !value)}
              aria-expanded={moreFieldsOpen}
              endIcon={moreFieldsOpen ? <ExpandLess /> : <ExpandMore />}
              sx={{ alignSelf: 'flex-start' }}
            >
              {moreFieldsOpen ? tUi("Fewer fields") : tUi("More fields")}
            </Button>
            <Collapse in={moreFieldsOpen} unmountOnExit>
              <Stack spacing={2}>
                <TextField name="description" label={tUi("Description")} value={editFormData.description} onChange={handleEditFormChange} fullWidth multiline rows={2} />
                <TextField name="logo_url" label={tUi("Logo URL")} value={editFormData.logo_url} onChange={handleEditFormChange} fullWidth />
                <TextField name="website" label={tUi("Website")} value={editFormData.website} onChange={handleEditFormChange} fullWidth />
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <TextField name="language" label={tUi("Language")} value={editFormData.language} onChange={handleEditFormChange} fullWidth />
                  <TextField name="country" label={tUi("Country")} value={editFormData.country} onChange={handleEditFormChange} fullWidth />
                </Stack>
              </Stack>
            </Collapse>
            <Stack direction="row" spacing={1}>
              <Button type="submit" variant="contained">
                {tUi("Save")}</Button>
              <Button onClick={() => void cancelEdit()}>{tUi("Cancel")}</Button>
            </Stack>
          </Stack></Box>
        </ContentSection>
      ) : null}

      <ContentSection
        title={tUi("Streams")}
        actions={
          <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap', gap: 1 }}>
            {draft && (
              <Button disabled={isSavingOrder} onClick={() => setOrderDraft(null)}>{tUi("Cancel")}</Button>
            )}
            <Button
              variant="contained"
              color="primary"
              size="small"
              startIcon={<SaveIcon />}
              disabled={!isOrderModified || isSavingOrder || streamCount < 2}
              onClick={() => void handleSaveOrder()}
            >
              {isSavingOrder ? tUi("Saving…") : tUi("Save order")}
            </Button>
            <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setOpenAssociateDialog(true)}>
              {tUi("Add stream")}</Button>
            <Button variant="outlined" size="small" onClick={() => setOpenBatchAssignDialog(true)}>
              {tUi("Add many")}</Button>
          </Stack>
        }
      >
        {streamCount === 0 ? (
          <Alert severity="info">{tUi("No streams yet. Add one so this channel can play.")}</Alert>
        ) : (
          <List sx={{ p: 0 }}>
            {orderedStreams.map((acestream, index) => (
              <ListItem
                key={acestream.id}
                divider
                onDragOver={(e) => {
                  if (!isSavingOrder && draggedStreamId.current !== null) {
                    e.preventDefault();
                    setDragOverStreamId(acestream.id);
                    e.dataTransfer.dropEffect = 'move';
                  }
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  if (draggedStreamId.current !== null) {
                    moveStream(draggedStreamId.current, acestream.id);
                  }
                  draggedStreamId.current = null;
                  setDragOverStreamId(null);
                }}
                sx={{
                  alignItems: 'center',
                  px: { xs: 1, sm: 2 },
                  pr: { xs: 1, sm: 12 },
                  bgcolor: dragOverStreamId === acestream.id ? 'action.selected' : 'transparent',
                  flexDirection: { xs: 'column', sm: 'row' },
                  '& .MuiListItemSecondaryAction-root': {
                    position: { xs: 'static', sm: 'absolute' },
                    transform: { xs: 'none', sm: 'translateY(-50%)' },
                    alignSelf: 'flex-end',
                  },
                }}
                secondaryAction={
                  <Box role="group" aria-label={tUi("Acestream actions for {{value0}}", { value0: acestream.name })}>
                    <Tooltip title={tUi("Play in the browser")}>
                      <IconButton
                        edge="end"
                        color="primary"
                        aria-label={tUi("play stream {{value0}}", { value0: acestream.name })}
                        onClick={() => setPlayerTarget({ contentId: acestream.id, title: acestream.name })}
                      >
                        <PlayArrowRounded />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={tUi("Remove from this channel")}>
                      <IconButton edge="end" color="error" aria-label={tUi("Remove acestream {{value0}}", { value0: acestream.name })} onClick={() => handleRemoveAcestream(acestream.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <Stack direction="row" alignItems="center" spacing={0.5} sx={{ mr: { xs: 0, sm: 2 }, mb: { xs: 1, sm: 0 }, alignSelf: { xs: 'flex-start', sm: 'center' } }}>
                  <IconButton
                    size="small"
                    draggable={!isSavingOrder}
                    disabled={isSavingOrder}
                    aria-label={tUi("Drag {{value0}}", { value0: acestream.name })}
                    sx={{ cursor: 'grab' }}
                    onDragStart={(e) => {
                      draggedStreamId.current = acestream.id;
                      e.dataTransfer.setData('text/plain', String(acestream.id));
                      e.dataTransfer.effectAllowed = 'move';
                    }}
                    onDragEnd={() => {
                      draggedStreamId.current = null;
                      setDragOverStreamId(null);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'ArrowUp' && index > 0) {
                        e.preventDefault();
                        moveStreamStep(index, 'up');
                      } else if (e.key === 'ArrowDown' && index < orderedStreams.length - 1) {
                        e.preventDefault();
                        moveStreamStep(index, 'down');
                      }
                    }}
                  >
                    <DragIndicator />
                  </IconButton>
                  <Typography
                    aria-label={tUi("Order {{value0}}", { value0: index + 1 })}
                    sx={{
                      minWidth: 28,
                      textAlign: 'center',
                      fontWeight: 700,
                      color: 'text.secondary',
                    }}
                  >
                    {index + 1}
                  </Typography>
                  <IconButton
                    size="small"
                    aria-label={tUi("Move {{value0}} up", { value0: acestream.name })}
                    disabled={isSavingOrder || index === 0}
                    onClick={() => moveStreamStep(index, 'up')}
                  >
                    <ArrowUpward fontSize="small" />
                  </IconButton>
                  <IconButton
                    size="small"
                    aria-label={tUi("Move {{value0}} down", { value0: acestream.name })}
                    disabled={isSavingOrder || index === orderedStreams.length - 1}
                    onClick={() => moveStreamStep(index, 'down')}
                  >
                    <ArrowDownward fontSize="small" />
                  </IconButton>
                </Stack>
                <ListItemText
                  primary={acestream.name}
                  primaryTypographyProps={{ fontWeight: 600 }}
                  secondary={
                    <Stack component="span" direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mt: 0.5 }}>
                      {acestream.is_online !== undefined && acestream.is_online !== null ? (
                        <Chip component="span" size="small" variant="outlined" label={acestream.is_online ? tUi("Online") : tUi("Offline")} color={acestream.is_online ? 'success' : 'error'} />
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

      <ContentSection title={tUi("Schedule")}>
        {!channel.epg_id ? (
          <Alert severity="info">{tUi("No EPG ID yet. Edit the channel and set one to see the schedule here.")}</Alert>
        ) : isResolvingEpg ? (
          <Box role="status" aria-live="polite">
            <LinearProgress sx={{ mb: 1 }} />
            <Typography variant="body2">{tUi("Finding the guide channel…")}</Typography>
          </Box>
        ) : epgChannel ? (
          <ScheduleView epgChannelId={epgChannel.id} />
        ) : (
          <Alert severity="warning">
            {isEpgResolveError
              ? tUi("Unable to look up the guide channel right now.")
              : tUi("No guide channel with id “{{value0}}” was found in the EPG sources. Check the ID or refresh the sources.", { value0: channel.epg_id })}
          </Alert>
        )}
      </ContentSection>

      <Dialog open={openAssociateDialog} onClose={() => void closeAssociation()} maxWidth="md" fullWidth>
        <DialogTitle>{tUi("Add a stream")}</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            disabled={isAssigning}
            label={tUi("Search by name, group, or ID")}
            fullWidth
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder={tUi("Type to search...")}
            variant="outlined"
            sx={{ mb: 2 }}
          />
          {isLoadingAcestreamCandidates ? (
            <Box sx={{ mb: 2 }} role="status" aria-live="polite">
              <LinearProgress sx={{ mb: 1 }} />
              <Typography variant="body2">{tUi("Loading Acestream candidates...")}</Typography>
            </Box>
          ) : null}
          {isErrorLoadingAcestreamCandidates ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {tUi("Unable to load Acestream candidates. Try searching again in a moment.")}</Alert>
          ) : null}
          <Alert severity="info" sx={{ mb: 2 }} role="status">
            {selectedAcestreams.length === 0
              ? tUi("Select one or more Acestream sources before assigning them.")
              : tUi('selectedStreamCount', { count: selectedAcestreams.length })}
          </Alert>
          <List sx={{ maxHeight: 350, overflow: 'auto' }}>
            {isErrorLoadingAcestreamCandidates ? null : acestreamCandidateItems.length === 0 ? (
              <ListItem>
                <ListItemText primary={tUi("No Acestream channels found.")} />
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
                      inputProps={{ 'aria-label': tUi('Select stream {{name}}', { name: acestream.name }) }}
                      disabled={isAssigning}
                      checked={selectedAcestreams.includes(acestream.id)}
                      onChange={(_event, checked) => {
                        setSelectedAcestreams((prev) => (checked ? [...prev, acestream.id] : prev.filter((item) => item !== acestream.id)));
                      }}
                    />
                  }
                >
                  <ListItemText primary={acestream.name} secondary={tUi('ID: {{id}} · Group: {{group}}', { id: acestream.id, group: acestream.group || tUi('None') })} />
                </ListItem>
              ))
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button disabled={isAssigning} onClick={() => void closeAssociation()} color="inherit">
            {tUi("Cancel")}</Button>
          <Button onClick={handleAssociateSelected} color="primary" variant="contained" disabled={isAssigning || selectedAcestreams.length === 0}>
            {tUi("Assign Selected")}</Button>
        </DialogActions>
      </Dialog>

      <BatchAcestreamAssignment
        open={openBatchAssignDialog}
        onClose={() => setOpenBatchAssignDialog(false)}
        tvChannelId={channelId}
        tvChannelName={channel.name}
      />

      <ChannelPlayerDialog
        tvChannelId={channelId}
        open={Boolean(playerTarget)}
        contentId={playerTarget?.contentId ?? null}
        title={playerTarget?.title ?? ''}
        onClose={() => setPlayerTarget(null)}
      />

      {confirmDialog}
    </Box>
  );
};

export default TVChannelDetail;
