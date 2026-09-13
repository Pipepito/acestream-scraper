import React, { useState } from 'react';
import {
  Box,
  Button,
  Divider,
  FormControlLabel,
  Grid,
  Slider,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';
import { useDownloadEPGXML } from '../hooks/useEPG';
import { EPGXMLGenerationParams } from '../services/epgService';
import { SnackbarSeverity } from '../hooks/useSnackbar';

interface EPGXmlOutputPanelProps {
  onNotify: (message: string, severity: SnackbarSeverity) => void;
}

const EPGXmlOutputPanel: React.FC<EPGXmlOutputPanelProps> = ({ onNotify }) => {
  // XML generation state
  const [xmlOptions, setXmlOptions] = useState<EPGXMLGenerationParams>({
    search_term: '',
    favorites_only: false,
    days_back: 1,
    days_forward: 7
  });

  const { mutateAsync: downloadEPGXML, isPending: isDownloadingXML } = useDownloadEPGXML();

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
      onNotify('EPG XML generation started', 'info');
    } catch (error) {
      onNotify(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    }
  };

  return (
    <Box sx={{ p: 0 }}>
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
    </Box>
  );
};

export default EPGXmlOutputPanel;
