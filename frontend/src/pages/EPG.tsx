import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from 'react-query';
import {
  Typography,
  Box,
  Paper,
  Tabs,
  Tab,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  FormControlLabel,
  Switch,
  Divider,
  Slider,
  Checkbox,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TablePagination,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Link as LinkIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import {
  useEPGSources,
  useEPGChannels,
  useCreateEPGSource,
  useUpdateEPGSource,
  useDeleteEPGSource,
  useRefreshAllEPGSources,
  useDownloadEPGXML
} from '../hooks/useEPG';
import { useAllTVChannels } from '../hooks/useTVChannels';
import { EPGSource, EPGChannel, EPGXMLGenerationParams, epgService } from '../services/epgService';
import { tvChannelService } from '../services/tvChannelService';
import PageHeader from '../components/layout/PageHeader';

interface EPGSourceFormData {
  url: string;
  name: string;
  enabled: boolean;
}

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
      id={`epg-tabpanel-${index}`}
      aria-labelledby={`epg-tab-${index}`}
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

const EPG: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  const [openSourceDialog, setOpenSourceDialog] = useState(false);
  const [isEditSource, setIsEditSource] = useState(false);
  const [editSourceId, setEditSourceId] = useState<number | null>(null);
  const [sourceFormData, setSourceFormData] = useState<EPGSourceFormData>({
    url: '',
    name: '',
    enabled: true
  });

  // XML generation state
  const [xmlOptions, setXmlOptions] = useState<EPGXMLGenerationParams>({
    search_term: '',
    favorites_only: false,
    days_back: 1,
    days_forward: 7
  });

  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'warning' | 'info'
  });

  // React Query hooks
  const { data: epgSources, isLoading: isLoadingSources } = useEPGSources();
  const [selectedSourceId, setSelectedSourceId] = useState<number | undefined>(undefined);
  const [channelPage, setChannelPage] = useState(1);
  const [channelPageSize, setChannelPageSize] = useState(50);

  const { data: epgChannelPage, isLoading: isLoadingChannels } = useEPGChannels(selectedSourceId, channelPage, channelPageSize);
  const { data: tvChannels } = useAllTVChannels(0, 1000);
  const { mutateAsync: createSource } = useCreateEPGSource();
  const { mutateAsync: updateSource } = useUpdateEPGSource(editSourceId || 0);
  const { mutateAsync: deleteSource } = useDeleteEPGSource();
  const { mutateAsync: refreshAllSources, isLoading: isRefreshingAll } = useRefreshAllEPGSources();
  const { mutateAsync: downloadEPGXML, isLoading: isDownloadingXML } = useDownloadEPGXML();

  // State for tracking which source is being refreshed
  const [refreshingSourceId, setRefreshingSourceId] = useState<number | null>(null);

  // State for EPG Channels selection
  const [selectedEPGChannelIds, setSelectedEPGChannelIds] = useState<number[]>([]);

  const epgChannels = useMemo(() => epgChannelPage?.items || [], [epgChannelPage]);
  const totalEPGChannels = epgChannelPage?.total || 0;
  const totalChannelPages = Math.max(1, Math.ceil(totalEPGChannels / channelPageSize));

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Source form handlers
  const handleAddSourceClick = () => {
    setIsEditSource(false);
    setEditSourceId(null);
    setSourceFormData({
      url: '',
      name: '',
      enabled: true
    });
    setOpenSourceDialog(true);
  };

  const handleEditSourceClick = (source: EPGSource) => {
    setIsEditSource(true);
    setEditSourceId(source.id);
    setSourceFormData({
      url: source.url,
      name: source.name,
      enabled: source.enabled
    });
    setOpenSourceDialog(true);
  };

  const handleCloseSourceDialog = () => {
    setOpenSourceDialog(false);
  };

  const handleSourceFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setSourceFormData({
      ...sourceFormData,
      [name]: type === 'checkbox' ? checked : value
    });
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

  const handleSourceFormSubmit = async () => {
    try {
      if (isEditSource && editSourceId) {
        await updateSource(sourceFormData);
        showSnackbar('EPG source updated successfully', 'success');
      } else {
        await createSource(sourceFormData);
        showSnackbar('EPG source added successfully', 'success');
      }
      handleCloseSourceDialog();
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  const handleDeleteSourceClick = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this EPG source?')) {
      try {
        await deleteSource(id);
        showSnackbar('EPG source deleted successfully', 'success');
      } catch (error) {
        showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
      }
    }
  };

  const handleRefreshSourceClick = async (id: number) => {
    try {
      setRefreshingSourceId(id);
      // Use the epgService directly since we need to pass the specific source ID
      const result = await epgService.refreshSource(id);
      if (result.success) {
        showSnackbar(`EPG source refreshed successfully. Found ${result.channels_found} channels and ${result.programs_found} programs.`, 'success');
      } else {
        showSnackbar(`Error refreshing EPG source: ${result.error || 'Unknown error'}`, 'error');
      }
      // Invalidate queries to refresh the data
      queryClient.invalidateQueries('epg-sources');
      queryClient.invalidateQueries('epg-channels');
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      setRefreshingSourceId(null);
    }
  };

  const handleRefreshAllClick = async () => {
    try {
      const results = await refreshAllSources();
      const successCount = results.filter(r => r.success).length;
      const failCount = results.length - successCount;

      if (failCount === 0) {
        showSnackbar(`All ${results.length} EPG sources refreshed successfully`, 'success');
      } else {
        showSnackbar(`${successCount} sources refreshed, ${failCount} failed`, 'warning');
      }
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  // Handle XML options changes
  const handleXmlOptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setXmlOptions({
      ...xmlOptions,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Handle day range slider change
  const handleDaysRangeChange = (event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      setXmlOptions({
        ...xmlOptions,
        days_back: Math.abs(newValue[0]),
        days_forward: newValue[1]
      });
    }
  };

  // Handle XML download
  const handleDownloadXML = async () => {
    try {
      await downloadEPGXML(xmlOptions);
      showSnackbar('EPG XML generation started', 'info');
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  // EPG Channels selection handlers
  // Build a set of mapped EPG XML IDs (or channel_xml_id)
  const mappedEpgXmlIds = useMemo(() => {
    if (!tvChannels) return new Set<string>();
    return new Set((tvChannels?.items || []).filter((c: any) => c.epg_id).map((c: any) => c.epg_id));
  }, [tvChannels]);

  const visibleUnmappedChannelIds = useMemo(
    () => epgChannels.filter((channel) => !mappedEpgXmlIds.has(channel.channel_xml_id)).map((channel) => channel.id),
    [epgChannels, mappedEpgXmlIds]
  );

  useEffect(() => {
    if (!isLoadingChannels && channelPage > totalChannelPages) {
      setChannelPage(1);
    }
  }, [channelPage, totalChannelPages, isLoadingChannels]);

  useEffect(() => {
    setSelectedEPGChannelIds([]);
  }, [selectedSourceId, channelPage, channelPageSize]);

  const isChannelMapped = (channel: EPGChannel) => mappedEpgXmlIds.has(channel.channel_xml_id);

  const handleSourceFilterChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value;
    setSelectedSourceId(value === 'all' ? undefined : Number(value));
    setChannelPage(1);
  };

  const handleChannelPageChange = (_event: unknown, page: number) => {
    setChannelPage(page + 1);
  };

  const handleChannelPageSizeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setChannelPageSize(Number(event.target.value));
    setChannelPage(1);
  };

  const handleSelectAllChannels = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedEPGChannelIds(visibleUnmappedChannelIds);
    } else {
      setSelectedEPGChannelIds([]);
    }
  };

  const handleSelectChannel = (id: number) => {
    const channel = epgChannels?.find(c => c.id === id);
    if (!channel || isChannelMapped(channel)) return;
    setSelectedEPGChannelIds((prev) =>
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]
    );
  };

  const handleBulkCreateTVChannels = async () => {
    if (!epgChannels) return;
    // Filter out already-mapped channels
    const unmappedIds = selectedEPGChannelIds.filter(id => {
      const channel = epgChannels.find(c => c.id === id);
      return channel && !isChannelMapped(channel);
    });
    if (unmappedIds.length === 0) {
      showSnackbar('No unmapped EPG channels selected.', 'warning');
      return;
    }
    try {
      const result = await tvChannelService.createFromEpg(unmappedIds);
      queryClient.invalidateQueries('tvChannels');
      queryClient.invalidateQueries('epg-channels');
      showSnackbar(
        `Created ${result.created_count} TV channels, skipped ${result.skipped_count}, auto-matched ${result.associated_count} Acestream channels`,
        'success'
      );
      setSelectedEPGChannelIds([]);
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  return (
    <Box sx={{ width: '100%', typography: 'body1' }}>
      <PageHeader
        title="EPG Management"
        subtitle="Manage source ingestion, map channels, and generate XML output."
      />

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          centered
        >
          <Tab label="Sources" />
          <Tab label="Channels" />
          <Tab label="XML Generation" />
        </Tabs>
      </Paper>

      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleAddSourceClick}
          >
            Add EPG Source
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefreshAllClick}
            disabled={isRefreshingAll}
          >
            Refresh All
          </Button>
        </Box>

        {isLoadingSources || isRefreshingAll ? (
          <LinearProgress sx={{ mb: 2 }} />
        ) : null}

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>URL</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Updated</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(epgSources || []).map((source) => (
                <TableRow key={source.id}>
                  <TableCell>{source.name}</TableCell>
                  <TableCell>{source.url}</TableCell>
                  <TableCell>
                    {source.enabled ? (
                      <Chip label="Enabled" color="success" size="small" />
                    ) : (
                      <Chip label="Disabled" color="default" size="small" />
                    )}
                    {source.error_count > 0 && (
                      <Chip
                        label={`Errors: ${source.error_count}`}
                        color="error"
                        size="small"
                        sx={{ ml: 1 }}
                        title={source.last_error}
                      />
                    )}
                  </TableCell>
                  <TableCell>
                    {source.last_updated ? (
                      formatDistanceToNow(new Date(source.last_updated), { addSuffix: true })
                    ) : (
                      'Never'
                    )}
                  </TableCell>
                  <TableCell>
                    <IconButton
                      color="primary"
                      onClick={() => handleRefreshSourceClick(source.id)}
                      disabled={refreshingSourceId === source.id}
                    >
                      <RefreshIcon />
                    </IconButton>
                    <IconButton color="secondary" onClick={() => handleEditSourceClick(source)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton color="error" onClick={() => handleDeleteSourceClick(source.id)}>
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {epgSources && epgSources.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No EPG sources found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6" gutterBottom>
            Available EPG Channels
          </Typography>
          <FormControl size="small" sx={{ minWidth: 240 }}>
            <InputLabel id="epg-source-filter-label">EPG Source</InputLabel>
            <Select
              labelId="epg-source-filter-label"
              label="EPG Source"
              value={selectedSourceId?.toString() ?? 'all'}
              onChange={handleSourceFilterChange}
            >
              <MenuItem value="all">All sources</MenuItem>
              {(epgSources || []).map((source) => (
                <MenuItem key={source.id} value={source.id.toString()}>
                  {source.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            color="primary"
            disabled={selectedEPGChannelIds.length === 0}
            onClick={handleBulkCreateTVChannels}
          >
            Create TV Channels ({selectedEPGChannelIds.length})
          </Button>
        </Box>

        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            {totalEPGChannels === 0
              ? 'Showing 0-0 of 0 channels'
              : `Showing ${(channelPage - 1) * channelPageSize + 1}-${Math.min(channelPage * channelPageSize, totalEPGChannels)} of ${totalEPGChannels} channels`}
          </Typography>
          <TablePagination
            component="div"
            count={totalEPGChannels}
            page={Math.max(channelPage - 1, 0)}
            onPageChange={handleChannelPageChange}
            rowsPerPage={channelPageSize}
            onRowsPerPageChange={handleChannelPageSizeChange}
            rowsPerPageOptions={[25, 50, 100]}
          />
        </Box>

        {isLoadingChannels ? (
          <LinearProgress sx={{ mb: 2 }} />
        ) : null}

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selectedEPGChannelIds.length > 0 && selectedEPGChannelIds.length < visibleUnmappedChannelIds.length}
                    checked={visibleUnmappedChannelIds.length > 0 && selectedEPGChannelIds.length === visibleUnmappedChannelIds.length}
                    onChange={handleSelectAllChannels}
                    inputProps={{ 'aria-label': 'select all EPG channels' }}
                  />
                </TableCell>
                <TableCell>Name</TableCell>
                <TableCell>XML ID</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Language</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {(epgChannels || []).map((channel) => (
                <TableRow key={channel.id} selected={selectedEPGChannelIds.includes(channel.id)}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedEPGChannelIds.includes(channel.id)}
                      onChange={() => handleSelectChannel(channel.id)}
                      inputProps={{ 'aria-label': `select EPG channel ${channel.name}` }}
                      disabled={isChannelMapped(channel)}
                    />
                  </TableCell>
                  <TableCell>
                    {channel.name}
                    {channel.icon_url && (
                      <Box
                        component="img"
                        src={channel.icon_url}
                        alt={channel.name}
                        sx={{ height: 30, marginLeft: 1.25, verticalAlign: 'middle' }}
                      />
                    )}
                  </TableCell>
                  <TableCell>{channel.channel_xml_id}</TableCell>
                  <TableCell>
                    {epgSources?.find(s => s.id === channel.epg_source_id)?.name || channel.epg_source_id}
                  </TableCell>
                  <TableCell>{channel.language || 'Unknown'}</TableCell>
                  <TableCell>
                    <IconButton
                      color="primary"
                      title="View Programs"
                      onClick={() => navigate(`/epg/channels/${channel.id}`)}
                    >
                      <VisibilityIcon />
                    </IconButton>
                    <IconButton color="primary" title="Link to TV Channel">
                      <LinkIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {epgChannels && epgChannels.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    No EPG channels found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Generate EPG XML
          </Typography>
          <Paper sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Search Term (Optional)"
                  name="search_term"
                  value={xmlOptions.search_term || ''}
                  onChange={handleXmlOptionChange}
                  placeholder="Filter channels by name"
                  variant="outlined"
                  margin="normal"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      name="favorites_only"
                      checked={!!xmlOptions.favorites_only}
                      onChange={handleXmlOptionChange}
                      color="primary"
                    />
                  }
                  label="Include Favorite Channels Only"
                  sx={{ mt: 2 }}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Date Range
                </Typography>
                <Box sx={{ px: 2 }}>
                  <Slider
                    value={[-(xmlOptions.days_back || 1), xmlOptions.days_forward || 7]}
                    min={-14}
                    max={14}
                    step={1}
                    onChange={handleDaysRangeChange}
                    valueLabelDisplay="auto"
                    marks={[
                      { value: -14, label: '14 days past' },
                      { value: -7, label: '1 week past' },
                      { value: 0, label: 'Today' },
                      { value: 7, label: '1 week future' },
                      { value: 14, label: '2 weeks future' }
                    ]}
                    valueLabelFormat={(value) => value < 0 ? `${Math.abs(value)}d past` : `${value}d future`}
                  />
                </Box>
                <Typography variant="body2" color="textSecondary" align="center">
                  Including {xmlOptions.days_back} days of past programs and {xmlOptions.days_forward} days of future programs
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<DownloadIcon />}
                    onClick={handleDownloadXML}
                    disabled={isDownloadingXML}
                    size="large"
                  >
                    {isDownloadingXML ? 'Generating...' : 'Generate and Download EPG XML'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Box>
      </TabPanel>

      {/* EPG Source Dialog */}
      <Dialog open={openSourceDialog} onClose={handleCloseSourceDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {isEditSource ? 'Edit EPG Source' : 'Add EPG Source'}
        </DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            name="name"
            label="Name"
            fullWidth
            value={sourceFormData.name}
            onChange={handleSourceFormChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="url"
            label="URL"
            fullWidth
            value={sourceFormData.url}
            onChange={handleSourceFormChange}
            sx={{ mb: 2 }}
            placeholder="https://example.com/epg.xml"
          />
          <FormControlLabel
            control={
              <Switch
                name="enabled"
                checked={sourceFormData.enabled}
                onChange={handleSourceFormChange}
              />
            }
            label="Enabled"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseSourceDialog}>Cancel</Button>
          <Button
            onClick={handleSourceFormSubmit}
            variant="contained"
            color="primary"
            disabled={!sourceFormData.url || !sourceFormData.name}
          >
            {isEditSource ? 'Update' : 'Add'}
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

export default EPG;
