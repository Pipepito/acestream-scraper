import React, { useState } from 'react';
import {
  Alert, Box, Button, Checkbox, Chip, Collapse, FormControl, FormControlLabel, FormHelperText, InputLabel, ListItemText,
  MenuItem, OutlinedInput, Select, Stack, TextField, Typography,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';
import type { PlaylistLink } from './usePlaylistLink';

interface PlaylistOptionsFormProps {
  link: PlaylistLink;
  formatsOpen: boolean;
  onToggleFormats: () => void;
  /** DOM id of the formats editor this form toggles; unique per mount. */
  formatsId?: string;
}

/** The playlist options: filters, stream link format and group filters. Shared by the page and the dialog. */
const PlaylistOptionsForm: React.FC<PlaylistOptionsFormProps> = ({ link, formatsOpen, onToggleFormats, formatsId = 'playlist-formats' }) => {
  const { filters, setFilters, search, setSearch, selectedBaseUrlId, setSelectedBaseUrlId, namedBaseUrls, loadingBaseUrls, baseUrlsError,
    channelGroups, loadingGroups, selectedFormat, isRelay, managed, onlineHelp } = link;
  const [showGroups, setShowGroups] = useState(false);

  const handleGroups = (key: 'include_groups' | 'exclude_groups') => (event: SelectChangeEvent<string[]>) => {
    setFilters((prev) => ({ ...prev, [key]: event.target.value as string[] }));
  };

  const renderGroupSelect = (label: string, key: 'include_groups' | 'exclude_groups') => (
    <FormControl fullWidth size="small">
      <InputLabel id={`${formatsId}-${key}-label`}>{label}</InputLabel>
      <Select
        labelId={`${formatsId}-${key}-label`}
        multiple
        value={filters[key] || []}
        onChange={handleGroups(key)}
        input={<OutlinedInput label={label} />}
        renderValue={(selected) => (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {(selected as string[]).map((value) => (
              <Chip key={value} label={value} size="small" />
            ))}
          </Box>
        )}
        disabled={loadingGroups}
      >
        {channelGroups.map((group) => (
          <MenuItem key={group} value={group}>
            <Checkbox checked={(filters[key] || []).includes(group)} size="small" />
            <ListItemText primary={group} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );

  return (
    <Stack spacing={2}>
      <Typography variant="sectionTitle" component="h3">
        Options
      </Typography>
      <TextField size="small" fullWidth label="Search channels" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Only include channels whose name contains…" />
      <Box>
        <FormControlLabel
          control={<Checkbox checked={filters.only_online ?? false} onChange={(e) => setFilters((prev) => ({ ...prev, only_online: e.target.checked }))} />}
          label="Only online channels"
        />
        <FormHelperText sx={{ mt: -0.5, ml: 4 }}>{onlineHelp}</FormHelperText>
      </Box>
      <FormControlLabel
        control={<Checkbox checked={filters.favorites_only ?? false} onChange={(e) => setFilters((prev) => ({ ...prev, favorites_only: e.target.checked }))} />}
        label="Favorite TV channels only"
      />
      <Box>
        <FormControlLabel
          control={<Checkbox checked={filters.include_unassigned ?? false} disabled={filters.favorites_only} onChange={(e) => setFilters((prev) => ({ ...prev, include_unassigned: e.target.checked }))} />}
          label="Include unassigned streams at the end"
        />
        <FormHelperText sx={{ mt: -0.5, ml: 4 }}>{filters.favorites_only ? 'Unassigned streams have no favorite TV channel.' : 'Streams without a TV channel appear last. In relay playlists they use individual stream URLs, without channel failover.'}</FormHelperText>
      </Box>
      <Box>
        <FormControlLabel
          control={<Checkbox checked={filters.per_source ?? false} disabled={!isRelay} onChange={(e) => setFilters((prev) => ({ ...prev, per_source: e.target.checked }))} />}
          label="List each source under its channel"
        />
        <FormHelperText sx={{ mt: -0.5, ml: 4 }}>{isRelay ? 'To switch source by hand. Each one opens alone, without failover.' : 'Only for TV channel relay formats.'}</FormHelperText>
      </Box>
      <FormControl fullWidth size="small">
        <InputLabel id={`${formatsId}-base-url-label`} shrink>Stream link format</InputLabel>
        <Select<number | '' | 'tv-relay'>
          labelId={`${formatsId}-base-url-label`}
          displayEmpty
          renderValue={(value) => value === '' ? 'Default' : value === 'tv-relay' ? 'TV channel relay (automatic failover)' : namedBaseUrls.find(entry => entry.id === value)?.name ?? 'Default'}
          value={managed ? 'tv-relay' : selectedBaseUrlId}
          onChange={(event) => {
            const value = event.target.value;
            setSelectedBaseUrlId(value === '' || value === 'tv-relay' ? value : Number(value));
          }}
          input={<OutlinedInput label="Stream link format" notched />}
          disabled={managed || loadingBaseUrls}
        >
          <MenuItem value="">Default</MenuItem>
          <MenuItem value="tv-relay">TV channel relay (automatic failover)</MenuItem>
          {namedBaseUrls.map((entry) => (
            <MenuItem key={entry.id} value={entry.id}>
              {entry.is_default ? `${entry.name} (default)` : entry.name}
            </MenuItem>
          ))}
        </Select>
        <FormHelperText>{managed ? 'User management requires application relay links to protect source credentials.' : 'Default uses your saved format, or acestream:// when none is saved.'}</FormHelperText>
      </FormControl>
      {selectedFormat ? <Typography variant="body2" sx={{ overflowWrap: 'anywhere' }}><strong>{selectedFormat.name}:</strong> {selectedFormat.pattern}</Typography> : null}
      {selectedFormat?.pattern.includes('{tv_channel_id}') ? <Alert severity="info">One entry per TV channel, using its stable ID. If playback fails, the relay selects another source when your player reconnects. Experimental transcoding recovery can be enabled in Integrations → Media servers → Tuner settings. Unassigned streams can be included below the TV channels using individual relay URLs.</Alert> : null}
      {baseUrlsError ? <Alert severity="warning">Could not load stream link formats. Try reloading the page.</Alert> : null}
      <Button onClick={onToggleFormats} aria-expanded={formatsOpen} aria-controls={formatsId} size="small">{namedBaseUrls.length ? 'Manage link formats' : 'Set up link formats'}</Button>
      <Box>
        <Button size="small" onClick={() => setShowGroups((value) => !value)} aria-expanded={showGroups} endIcon={showGroups ? <ExpandLess /> : <ExpandMore />}>
          Group filters
        </Button>
        <Collapse in={showGroups} mountOnEnter unmountOnExit>
          <Stack spacing={2} sx={{ mt: 1.5 }}>
            {renderGroupSelect('Include groups', 'include_groups')}
            {renderGroupSelect('Exclude groups', 'exclude_groups')}
          </Stack>
        </Collapse>
      </Box>
    </Stack>
  );
};

export default PlaylistOptionsForm;
