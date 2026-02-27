import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import BatchAcestreamAssignment from '../components/BatchAcestreamAssignment';
import EPGProgramsTable from '../components/EPGProgramsTable';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Paper,
  FormControlLabel,
  Switch,
  AppBar,
  Toolbar,
  Link,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Link as LinkIcon,
  PlayArrow as PlayIcon,
  ArrowBack as BackIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { useTVChannel, useTVChannelAcestreams, useAssociateAcestream, useRemoveAcestreamAssociation, useUpdateTVChannel } from '../hooks/useTVChannels';
import { AcestreamChannel } from '../types/channelTypes';
import { Link as RouterLink } from 'react-router-dom';
import { useAcestreamChannels } from '../hooks/useChannels';
import '../styles/TVChannelDetail.css';

const TVChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const channelId = id ? parseInt(id) : 0;

  const { data: channel, isLoading, isError } = useTVChannel(channelId);
  const { data: acestreams } = useTVChannelAcestreams(channelId);
  const associateAcestreamMutation = useAssociateAcestream();
  const removeAcestreamMutation = useRemoveAcestreamAssociation();

  const [openAssociateDialog, setOpenAssociateDialog] = useState(false);
  const [openBatchAssignDialog, setOpenBatchAssignDialog] = useState(false);
  const [aceStreamId, setAceStreamId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAcestreams, setSelectedAcestreams] = useState<string[]>([]);
  const { data: acestreamCandidates, isLoading: isLoadingAcestreamCandidates } = useAcestreamChannels(
    searchTerm ? { search: searchTerm } : {},
    { staleTime: 1000 * 60 }
  );

  const handleGoBack = () => {
    navigate('/tv-channels');
  };

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
    is_favorite: false
  });
  const updateChannelMutation = useUpdateTVChannel();

  const handleEdit = () => {
    if (channel) {
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
        is_favorite: channel.is_favorite
      });
      setIsEditing(true);
    }
  };

  const handleAssociateAcestream = async () => {
    if (!aceStreamId) return;

    try {
      await associateAcestreamMutation.mutateAsync({
        tvChannelId: channelId,
        aceStreamId
      });
      setAceStreamId('');
      setOpenAssociateDialog(false);
    } catch (error) {
      console.error('Error associating acestream:', error);
    }
  };

  const handleRemoveAcestream = async (aceStreamId: string) => {
    if (window.confirm('Are you sure you want to remove this acestream?')) {
      try {
        await removeAcestreamMutation.mutateAsync({
          tvChannelId: channelId,
          aceStreamId
        });
      } catch (error) {
        console.error('Error removing acestream:', error);
      }
    }
  };

  const handleEditFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setEditFormData({
      ...editFormData,
      [name]: type === 'checkbox' ? checked : value
    });
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
          is_favorite: editFormData.is_favorite
        }
      });
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating TV channel:', error);
    }
  };

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !channel) {
    return (
      <Box p={3}>
        <Typography color="error">Error loading TV channel details.</Typography>
        <Button startIcon={<BackIcon />} onClick={handleGoBack} sx={{ mt: 2 }}>
          Back to TV Channels
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <AppBar position="static" color="default" elevation={1} sx={{ mb: 2 }}>
        <Toolbar sx={{ flexDirection: isMobile ? 'column' : 'row', gap: 2 }}>
          <Link component={RouterLink} to="/acestream-channels" underline="none" color="inherit" sx={{ fontWeight: 600, fontSize: 18 }}>
            Acestream Channels
          </Link>
          <Link component={RouterLink} to="/tv-channels" underline="none" color="inherit" sx={{ fontWeight: 600, fontSize: 18 }}>
            TV Channels
          </Link>
        </Toolbar>
      </AppBar>

      <Box p={3}>
        <Box display="flex" alignItems="center" mb={3}>
          <Button startIcon={<BackIcon />} onClick={handleGoBack}>
            Back
          </Button>
          <Typography variant="h4" sx={{ ml: 2, flexGrow: 1 }}>
            {channel.name}
          </Typography>
          {isEditing ? (
            <>
              <Button
                variant="contained"
                color="primary"
                onClick={handleSaveEdit}
                sx={{ mr: 1 }}
              >
                Save
              </Button>
              <Button
                variant="outlined"
                color="inherit"
                onClick={() => setIsEditing(false)}
                sx={{ mr: 1 }}
              >
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button
                startIcon={<EditIcon />}
                variant="outlined"
                color="primary"
                onClick={handleEdit}
                sx={{ mr: 1 }}
              >
                Edit
              </Button>
            </>
          )}
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                {!isEditing && channel.logo_url && (
                  <Box mb={3} display="flex" justifyContent="center">
                    <img
                      src={channel.logo_url}
                      alt={`${channel.name} logo`}
                      className="channel-logo-img"
                    />
                  </Box>
                )}

                <Typography variant="h6" gutterBottom>
                  Channel Information
                </Typography>

                {isEditing ? (
                  <Box mt={2}>
                    <TextField
                      label="Name"
                      name="name"
                      value={editFormData.name}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                      required
                    />

                    <TextField
                      label="Logo URL"
                      name="logo_url"
                      value={editFormData.logo_url}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <TextField
                      label="Description"
                      name="description"
                      value={editFormData.description}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                      multiline
                      rows={3}
                    />

                    <TextField
                      label="Category"
                      name="category"
                      value={editFormData.category}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <TextField
                      label="Language"
                      name="language"
                      value={editFormData.language}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <TextField
                      label="Country"
                      name="country"
                      value={editFormData.country}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <TextField
                      label="Website"
                      name="website"
                      value={editFormData.website}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <TextField
                      label="EPG ID"
                      name="epg_id"
                      value={editFormData.epg_id}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <TextField
                      label="Channel Number"
                      name="channel_number"
                      type="number"
                      value={editFormData.channel_number}
                      onChange={handleEditFormChange}
                      fullWidth
                      margin="dense"
                    />

                    <Box display="flex" mt={2}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={editFormData.is_active}
                            onChange={handleEditFormChange}
                            name="is_active"
                            color="primary"
                          />
                        }
                        label="Active"
                      />

                      <FormControlLabel
                        control={
                          <Switch
                            checked={editFormData.is_favorite}
                            onChange={handleEditFormChange}
                            name="is_favorite"
                            color="primary"
                          />
                        }
                        label="Favorite"
                      />
                    </Box>
                  </Box>
                ) : (
                  <Box mt={2}>
                    {channel.category && (
                      <Box display="flex" mb={1}>
                        <Typography variant="body1" fontWeight="bold" minWidth={100}>
                          Category:
                        </Typography>
                        <Typography variant="body1">
                          {channel.category}
                        </Typography>
                      </Box>
                    )}

                    {channel.language && (
                      <Box display="flex" mb={1}>
                        <Typography variant="body1" fontWeight="bold" minWidth={100}>
                          Language:
                        </Typography>
                        <Typography variant="body1">
                          {channel.language}
                        </Typography>
                      </Box>
                    )}

                    {channel.country && (
                      <Box display="flex" mb={1}>
                        <Typography variant="body1" fontWeight="bold" minWidth={100}>
                          Country:
                        </Typography>
                        <Typography variant="body1">
                          {channel.country}
                        </Typography>
                      </Box>
                    )}

                    {channel.epg_id && (
                      <Box display="flex" mb={1}>
                        <Typography variant="body1" fontWeight="bold" minWidth={100}>
                          EPG ID:
                        </Typography>
                        <Typography variant="body1">
                          {channel.epg_id}
                        </Typography>
                      </Box>
                    )}

                    {channel.channel_number !== undefined && (
                      <Box display="flex" mb={1}>
                        <Typography variant="body1" fontWeight="bold" minWidth={100}>
                          Number:
                        </Typography>
                        <Typography variant="body1">
                          {channel.channel_number}
                        </Typography>
                      </Box>
                    )}

                    <Box display="flex" mb={1}>
                      <Typography variant="body1" fontWeight="bold" minWidth={100}>
                        Status:
                      </Typography>
                      <Chip
                        size="small"
                        label={channel.is_active ? 'Active' : 'Inactive'}
                        color={channel.is_active ? 'success' : 'error'}
                      />
                    </Box>

                    <Box display="flex" mb={1}>
                      <Typography variant="body1" fontWeight="bold" minWidth={100}>
                        Favorite:
                      </Typography>
                      <Chip
                        size="small"
                        label={channel.is_favorite ? 'Yes' : 'No'}
                        color={channel.is_favorite ? 'primary' : 'default'}
                      />
                    </Box>
                  </Box>
                )}

                {!isEditing && channel.website && (
                  <Box mt={2}>
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
                  </Box>
                )}
              </CardContent>
            </Card>

            {!isEditing && channel.description && (
              <Paper sx={{ mt: 3, p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body2">
                  {channel.description}
                </Typography>
              </Paper>
            )}
          </Grid>

          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Acestream Channels ({channel.acestream_channels.length})
                </Typography>
                <Box>
                  <Button
                    startIcon={<AddIcon />}
                    variant="contained"
                    color="primary"
                    size="small"
                    onClick={() => setOpenAssociateDialog(true)}
                    sx={{ mr: 1 }}
                  >
                    Add Single
                  </Button>
                  <Button
                    variant="outlined"
                    color="primary"
                    size="small"
                    onClick={() => setOpenBatchAssignDialog(true)}
                  >
                    Batch Add
                  </Button>
                </Box>
              </Box>

              <Divider />

              {channel.acestream_channels.length === 0 ? (
                <Box py={3} textAlign="center">
                  <Typography color="textSecondary">
                    No acestream channels associated with this TV channel yet.
                  </Typography>
                </Box>
              ) : (
                <List>
                  {channel.acestream_channels.map((acestream: AcestreamChannel) => (
                    <ListItem key={acestream.channel_id}>
                      <ListItemText
                        primary={acestream.name}
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="textSecondary">
                              ID: {acestream.channel_id}
                            </Typography>
                            <br />
                            <Typography component="span" variant="body2" color="textSecondary">
                              Group: {acestream.group || 'None'}
                            </Typography>
                            {acestream.is_online !== undefined && (
                              <>
                                <br />
                                <Chip
                                  size="small"
                                  label={acestream.is_online ? 'Online' : 'Offline'}
                                  color={acestream.is_online ? 'success' : 'error'}
                                />
                              </>
                            )}
                          </>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          color="primary"
                        >
                          <PlayIcon />
                        </IconButton>
                        <IconButton
                          edge="end"
                          color="error"
                          onClick={() => handleRemoveAcestream(acestream.channel_id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>

            {/* EPG Programs Schedule Section */}
            {channel.epg_id && (
              <Box mt={4}>
                <Typography variant="h6" gutterBottom>
                  EPG Program Schedule
                </Typography>
                <EPGProgramsTable epgId={channel.epg_id} />
              </Box>
            )}
          </Grid>
        </Grid>

        {/* Associate Acestream Dialog */}
        <Dialog open={openAssociateDialog} onClose={() => setOpenAssociateDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Associate Acestream Channel</DialogTitle>
          <DialogContent>
            <TextField
              margin="dense"
              label="Search by name, group, or ID"
              fullWidth
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Type to search..."
              variant="outlined"
              sx={{ mb: 2 }}
            />
            {isLoadingAcestreamCandidates ? (
              <Box display="flex" justifyContent="center" my={2}><CircularProgress /></Box>
            ) : (
              <List sx={{ maxHeight: 350, overflow: 'auto' }}>
                {(acestreamCandidates?.length ?? 0) === 0 ? (
                  <ListItem>
                    <ListItemText primary="No Acestream channels found." />
                  </ListItem>
                ) : (
                  (acestreamCandidates || []).map((acestream: any) => (
                    <ListItem
                      key={acestream.id}
                      button
                      selected={selectedAcestreams.includes(acestream.id)}
                      onClick={() => {
                        setSelectedAcestreams((prev) =>
                          prev.includes(acestream.id)
                            ? prev.filter(id => id !== acestream.id)
                            : [...prev, acestream.id]
                        );
                      }}
                    >
                      <ListItemText
                        primary={acestream.name}
                        secondary={`ID: ${acestream.id} | Group: ${acestream.group || 'None'}`}
                      />
                      <ListItemSecondaryAction>
                        <IconButton
                          edge="end"
                          color="primary"
                          onClick={async () => {
                            try {
                              await associateAcestreamMutation.mutateAsync({
                                tvChannelId: channelId,
                                aceStreamId: acestream.id
                              });
                              setOpenAssociateDialog(false);
                            } catch (error) {
                              console.error('Error associating acestream:', error);
                            }
                          }}
                        >
                          <AddIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))
                )}
              </List>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenAssociateDialog(false)} color="inherit">
              Cancel
            </Button>
            <Button
              onClick={async () => {
                for (const aceStreamId of selectedAcestreams) {
                  try {
                    await associateAcestreamMutation.mutateAsync({
                      tvChannelId: channelId,
                      aceStreamId
                    });
                  } catch (error) {
                    console.error('Error associating acestream:', error);
                  }
                }
                setOpenAssociateDialog(false);
                setSelectedAcestreams([]);
              }}
              color="primary"
              variant="contained"
              disabled={selectedAcestreams.length === 0}
            >
              Assign Selected
            </Button>
          </DialogActions>
        </Dialog>

        {/* Batch Assignment Dialog */}
        <BatchAcestreamAssignment
          open={openBatchAssignDialog}
          onClose={() => setOpenBatchAssignDialog(false)}
          tvChannelId={channelId}
          tvChannelName={channel.name}
        />
      </Box>
    </Box>
  );
};

export default TVChannelDetail;
