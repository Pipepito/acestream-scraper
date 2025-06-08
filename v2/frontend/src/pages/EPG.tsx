import React, { useState } from 'react';
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
  Card,
  CardContent,
  CardActions,
  FormControlLabel,
  Switch
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { 
  useEPGSources, 
  useEPGChannels, 
  useCreateEPGSource, 
  useUpdateEPGSource, 
  useDeleteEPGSource, 
  useRefreshEPGSource, 
  useRefreshAllEPGSources,
  useMapEPGChannel
} from '../hooks/useEPG';
import { EPGSource, EPGChannel, CreateEPGSourceDTO, UpdateEPGSourceDTO } from '../services/epgService';

interface EPGSourceFormData {
  url: string;
  name: string;
  enabled: boolean;
}

interface EPGChannelMappingFormData {
  epg_channel_id: number;
  tv_channel_id: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Placeholder data until we have backend services
const mockEPGSources: EPGSource[] = [
  {
    id: 1,
    url: 'https://example.com/epg1.xml',
    name: 'XMLTV Guide',
    enabled: true,
    last_updated: '2023-06-15T14:30:00Z',
    error_count: 0,
    last_error: undefined
  },
  {
    id: 2,
    url: 'https://example.com/epg2.xml',
    name: 'Sports EPG',
    enabled: false,
    last_updated: '2023-06-10T08:45:00Z',
    error_count: 2,
    last_error: 'Failed to download XML file'
  }
];

const mockEPGChannels: EPGChannel[] = [
  {
    id: 1,
    epg_source_id: 1,
    channel_xml_id: 'espn.com',
    name: 'ESPN',
    icon_url: 'https://example.com/espn.png',
    language: 'en',
    created_at: '2023-01-15T00:00:00Z',
    updated_at: '2023-06-15T14:30:00Z'
  },
  {
    id: 2,
    epg_source_id: 1,
    channel_xml_id: 'cnn.com',
    name: 'CNN',
    icon_url: 'https://example.com/cnn.png',
    language: 'en',
    created_at: '2023-01-15T00:00:00Z',
    updated_at: '2023-06-15T14:30:00Z'
  }
];

const TabPanel = (props: TabPanelProps) => {
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
};

const EPG: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [openSourceDialog, setOpenSourceDialog] = useState(false);
  const [isEditSource, setIsEditSource] = useState(false);
  const [currentSourceId, setCurrentSourceId] = useState<number | null>(null);
  const [sourceFormData, setSourceFormData] = useState<EPGSourceFormData>({
    url: '',
    name: '',
    enabled: true
  });
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  
  // For now we'll use the mock data, but these would be replaced with React Query hooks
  const isLoading = false;
  const epgSources = mockEPGSources;
  const epgChannels = mockEPGChannels;

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenSourceDialog = (edit = false, source?: EPGSource) => {
    setIsEditSource(edit);
    if (edit && source) {
      setSourceFormData({
        url: source.url,
        name: source.name,
        enabled: source.enabled
      });
      setCurrentSourceId(source.id);
    } else {
      setSourceFormData({
        url: '',
        name: '',
        enabled: true
      });
      setCurrentSourceId(null);
    }
    setOpenSourceDialog(true);
  };

  const handleCloseSourceDialog = () => {
    setOpenSourceDialog(false);
  };

  const handleSourceFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked, type } = e.target;
    setSourceFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSourceFormSubmit = () => {
    // This would call a mutation function to save the data
    setSnackbar({
      open: true,
      message: isEditSource ? 'EPG Source updated successfully' : 'EPG Source added successfully',
      severity: 'success'
    });
    handleCloseSourceDialog();
  };

  const handleDeleteSource = (id: number) => {
    // This would call a mutation function to delete the EPG source
    if (confirm('Are you sure you want to delete this EPG source?')) {
      setSnackbar({
        open: true,
        message: 'EPG Source deleted successfully',
        severity: 'success'
      });
    }
  };

  const handleRefreshEPG = (id: number) => {
    // This would trigger a refresh of the EPG data
    setSnackbar({
      open: true,
      message: 'EPG refresh started',
      severity: 'success'
    });
  };

  const closeSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Electronic Program Guide (EPG)
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="EPG tabs">
          <Tab label="EPG Sources" />
          <Tab label="Channel Mappings" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            EPG Sources
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<AddIcon />}
            onClick={() => handleOpenSourceDialog(false)}
          >
            Add EPG Source
          </Button>
        </Box>

        <Grid container spacing={3}>
          {isLoading ? (
            <Grid item xs={12}>
              <LinearProgress />
            </Grid>
          ) : (
            epgSources.map((source) => (
              <Grid item xs={12} md={6} lg={4} key={source.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" component="div">
                      {source.name}
                      {source.enabled ? 
                        <Chip 
                          label="Enabled" 
                          color="success" 
                          size="small" 
                          sx={{ ml: 1 }} 
                        /> : 
                        <Chip 
                          label="Disabled" 
                          color="default" 
                          size="small" 
                          sx={{ ml: 1 }} 
                        />
                      }
                    </Typography>
                    <Typography color="text.secondary" sx={{ mt: 1 }}>
                      <LinkIcon fontSize="small" sx={{ mr: 0.5, verticalAlign: 'middle' }} />
                      {source.url}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 2 }}>
                      Last updated: {source.last_updated ? 
                        formatDistanceToNow(new Date(source.last_updated), { addSuffix: true }) : 
                        'Never'
                      }
                    </Typography>                    {source.error_count > 0 && source.last_error && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        {source.last_error}
                      </Alert>
                    )}
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      startIcon={<RefreshIcon />}
                      onClick={() => handleRefreshEPG(source.id)}
                    >
                      Refresh
                    </Button>
                    <Button 
                      size="small"
                      startIcon={<EditIcon />}
                      onClick={() => handleOpenSourceDialog(true, source)}
                    >
                      Edit
                    </Button>
                    <Button 
                      size="small" 
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleDeleteSource(source.id)}
                    >
                      Delete
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))
          )}

          {epgSources.length === 0 && !isLoading && (
            <Grid item xs={12}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body1">
                  No EPG sources found. Add an EPG source to get started.
                </Typography>
              </Paper>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            EPG Channel Mappings
          </Typography>
        </Box>

        <Paper sx={{ width: '100%', overflow: 'hidden' }}>
          {isLoading && <LinearProgress />}
          
          <TableContainer sx={{ maxHeight: 640 }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>EPG Channel</TableCell>
                  <TableCell>XML ID</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Mapped TV Channels</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {epgChannels.length > 0 ? (
                  epgChannels.map((channel) => {
                    const source = epgSources.find(s => s.id === channel.epg_source_id);
                    return (
                      <TableRow key={channel.id} hover>
                        <TableCell>
                          <Box display="flex" alignItems="center">
                            {channel.icon_url && (
                              <Box 
                                component="img" 
                                src={channel.icon_url} 
                                alt={channel.name}
                                sx={{ width: 30, height: 30, mr: 1 }}
                              />
                            )}
                            {channel.name}
                          </Box>
                        </TableCell>
                        <TableCell>{channel.channel_xml_id}</TableCell>
                        <TableCell>{source?.name || 'Unknown'}</TableCell>
                        <TableCell>
                          <Chip label="Not mapped yet" variant="outlined" />
                        </TableCell>
                        <TableCell>
                          <Button 
                            size="small" 
                            variant="outlined"
                            startIcon={<LinkIcon />}
                          >
                            Map to TV Channel
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      {isLoading ? 'Loading...' : 'No EPG channels found'}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
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
