import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Snackbar,
  Grid,
  Card,
  CardContent,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Switch,
  Tabs,
  Tab,
  Pagination,
  Stack
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Tv as TvIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Link as LinkIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { format, parseISO } from 'date-fns';
import {
  useEPGChannel,
  useEPGPrograms,
  useEPGStringMappings,
  useAddEPGStringMapping,
  useDeleteEPGStringMapping,
  useMapEPGChannel,
  useUnmapEPGChannel
} from '../hooks/useEPG';
import { useAllTVChannels } from '../hooks/useTVChannels';
import { EPGProgram, EPGStringMapping } from '../services/epgService';
import { TVChannel } from '../types/tvChannelTypes';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`epg-channel-tabpanel-${index}`}
      aria-labelledby={`epg-channel-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface StringMappingFormData {
  search_pattern: string;
  is_exclusion: boolean;
}

const EPGChannelDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const channelId = parseInt(id || '0', 10);

  // State management
  const [tabValue, setTabValue] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [programsPerPage] = useState(50);
  const [dateRange, setDateRange] = useState({
    start: new Date().toISOString().split('T')[0],
    end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
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
  const [creatingTV, setCreatingTV] = useState(false);

  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'warning' | 'info'
  });

  // API hooks
  const { data: channel, isLoading: isLoadingChannel } = useEPGChannel(channelId);
  const { data: programs, isLoading: isLoadingPrograms } = useEPGPrograms(
    channelId,
    dateRange.start,
    dateRange.end
  );
  const { data: stringMappings, isLoading: isLoadingMappings } = useEPGStringMappings(channelId);
  const { data: tvChannels } = useAllTVChannels();

  // Mutations
  const { mutateAsync: addStringMapping } = useAddEPGStringMapping(channelId);
  const { mutateAsync: deleteStringMapping } = useDeleteEPGStringMapping(channelId);
  const { mutateAsync: mapChannel } = useMapEPGChannel();
  const { mutateAsync: unmapChannel } = useUnmapEPGChannel();

  // Pagination
  const totalPages = Math.ceil((programs?.length || 0) / programsPerPage);
  const paginatedPrograms = programs?.slice(
    (currentPage - 1) * programsPerPage,
    currentPage * programsPerPage
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

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
    try {
      await addStringMapping({
        pattern: stringMappingFormData.search_pattern,
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
    if (!selectedTVChannel) return;

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
      <Box sx={{ width: '100%', p: 3 }}>
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
          EPG channel not found
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={() => navigate('/epg')} sx={{ mr: 2 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          EPG Channel: {channel.name}
        </Typography>
      </Box>

      {/* Channel Information Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Channel Information
              </Typography>
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
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
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
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          centered
        >
          <Tab label="Programs" />
          <Tab label="String Mappings" />
        </Tabs>
      </Paper>

      {/* Programs Tab */}
      <TabPanel value={tabValue} index={0}>
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
          <LinearProgress sx={{ mb: 2 }} />
        ) : null}

        <TableContainer component={Paper}>
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
                  <TableCell>
                    {formatDateTime(program.start_time)}
                  </TableCell>
                  <TableCell>
                    {formatDateTime(program.end_time)}
                  </TableCell>
                  <TableCell>
                    {formatDuration(program.start_time, program.end_time)}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {program.title}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {program.subtitle && (
                      <Typography variant="body2" color="text.secondary">
                        {program.subtitle}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {program.category && (
                      <Chip label={program.category} size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    {program.description && (
                      <Typography variant="body2" color="text.secondary">
                        {program.description.length > 100
                          ? `${program.description.substring(0, 100)}...`
                          : program.description}
                      </Typography>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {programs && programs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No programs found for the selected date range
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {totalPages > 1 && (
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
        )}
      </TabPanel>

      {/* String Mappings Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">
            String Mappings
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => setOpenStringMappingDialog(true)}
          >
            Add String Mapping
          </Button>
        </Box>

        {isLoadingMappings ? (
          <LinearProgress sx={{ mb: 2 }} />
        ) : null}

        <TableContainer component={Paper}>
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
                    <IconButton
                      color="error"
                      onClick={() => handleDeleteStringMapping(mapping.id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {stringMappings && stringMappings.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} align="center">
                    No string mappings found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

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
          <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
            {(tvChannels?.items || []).map((tvChannel: TVChannel) => (
              <Box
                key={tvChannel.id}
                sx={{
                  p: 2,
                  border: 1,
                  borderColor: selectedTVChannel === tvChannel.id ? 'primary.main' : 'grey.300',
                  borderRadius: 1,
                  mb: 1,
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'grey.50'
                  }
                }}
                onClick={() => setSelectedTVChannel(tvChannel.id)}
              >
                <Typography variant="body1" fontWeight="bold">
                  {tvChannel.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Category: {tvChannel.category || 'None'}
                </Typography>
              </Box>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenMappingDialog(false)}>Cancel</Button>
          <Button
            onClick={handleMapToTVChannel}
            variant="contained"
            color="primary"
            disabled={!selectedTVChannel}
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
            onClick={async () => {
              setCreatingTV(true);
              try {
                const formWithEpgId = { ...createTVForm, epg_id: channel.channel_xml_id };
                const res = await import('../services/tvChannelService').then(({ tvChannelService }) =>
                  tvChannelService.create(formWithEpgId)
                );
                showSnackbar('TV Channel created and mapped to EPG', 'success');
                setOpenCreateTVDialog(false);
              } catch (err) {
                showSnackbar('Failed to create TV Channel', 'error');
              } finally {
                setCreatingTV(false);
              }
            }}
            color="primary"
            variant="contained"
            disabled={!createTVForm.name || creatingTV}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
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
