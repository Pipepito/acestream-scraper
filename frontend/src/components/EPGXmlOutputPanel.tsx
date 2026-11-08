import { getErrorMessage } from '../utils/errorUtils';
import { useUiText } from '../i18n/useUiText';
import React, { useState, useRef } from 'react';
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
  const tUi = useUiText();
  const submitting = useRef(false);
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

  // Handle XML download
  const handleDownloadXML = async () => {
    if (submitting.current) return;
    submitting.current = true;
    try {
      await downloadEPGXML(xmlOptions);
      onNotify(tUi('EPG XML generation started'), 'info');
    } catch (error) {
      onNotify(getErrorMessage(error), 'error');
    } finally {
      submitting.current = false;
    }
  };

  return (
    <Box sx={{ p: 0 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth
            label={tUi("Search Term (Optional)")}
            name="search_term"
            value={xmlOptions.search_term || ''}
            onChange={handleXmlOptionChange}
            placeholder={tUi("Filter channels by name")}
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
            label={tUi("Include Favorite Channels Only")}
            sx={{ mt: 2 }}
          />
        </Grid>

        <Grid item xs={12}>
          <Typography variant="subtitle1" gutterBottom>
            {tUi("Date Range")}</Typography>
          <Box sx={{ px: 2 }}>
            {(['days_back', 'days_forward'] as const).map(field => <Box key={field} sx={{ mb: 2 }}>
              <Typography id={`xml-${field}-label`} variant="body2">{field === 'days_back' ? tUi('Past programmes (days)') : tUi('Future programmes (days)')}</Typography>
              <Slider
                aria-labelledby={`xml-${field}-label`}
                value={xmlOptions[field] ?? (field === 'days_back' ? 1 : 7)}
                min={0} max={14} step={1}
                onChange={(_, value) => { if (typeof value === 'number') setXmlOptions(previous => ({ ...previous, [field]: value })); }}
                valueLabelDisplay="auto"
                getAriaValueText={count => tUi('{{count}} day', { count })}
                marks={[{ value: 0, label: '0' }, { value: 7, label: '7' }, { value: 14, label: '14' }]}
              />
            </Box>)}
          </Box>
          <Typography variant="body2" color="textSecondary" align="center">
            {tUi('Including {{past}} days of past programmes and {{future}} days of future programmes.', { past: xmlOptions.days_back ?? 1, future: xmlOptions.days_forward ?? 7 })}
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
              {isDownloadingXML ? tUi("Generating...") : tUi("Generate and Download EPG XML")}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EPGXmlOutputPanel;
