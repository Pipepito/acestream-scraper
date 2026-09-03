import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from '@mui/material';
import { useAcestreamChannels } from '../../hooks/useChannels';
import { usePlayOnRemotePlayer } from '../../hooks/useRemotePlayers';
import { useTVChannelCatalog } from '../../hooks/useTVChannels';
import { ApiError } from '../../services/apiErrors';
import type { RemotePlayer } from '../../services/remotePlayerService';
import { describeRemotePlayerError } from './playerCopy';

export interface ChannelPickerDialogProps {
  open: boolean;
  player: RemotePlayer | null;
  onClose: () => void;
}

interface PickerOption {
  key: string;
  label: string;
  secondary: string;
  contentId: string;
}

const describeOnline = (isOnline: boolean | null | undefined): string =>
  isOnline ? 'Online' : isOnline === false ? 'Offline' : 'Unchecked';

const useDebounced = (value: string, ms: number) => {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = window.setTimeout(() => setDebounced(value), ms);
    return () => window.clearTimeout(handle);
  }, [value, ms]);
  return debounced;
};

/** Pick a TV channel (best stream) or a raw stream and send it to a remote player. */
const ChannelPickerDialog: React.FC<ChannelPickerDialogProps> = ({ open, player, onClose }) => {
  const [mode, setMode] = useState<'tv' | 'streams'>('tv');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<PickerOption | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebounced(search, 300);
  const tv = useTVChannelCatalog({ search: debounced });
  const streams = useAcestreamChannels(
    { search: debounced || undefined, is_active: true, page: 1, page_size: 50 },
    { enabled: open && mode === 'streams' }
  );
  const play = usePlayOnRemotePlayer();

  // The dialog stays mounted between openings; start each one empty.
  useEffect(() => {
    if (!open) return;
    setSearch('');
    setSelected(null);
    setError(null);
  }, [open]);

  const options = useMemo<PickerOption[]>(() => {
    if (mode === 'tv') {
      return (tv.data ?? [])
        .filter((channel) => channel.is_active && channel.acestream_channels.length > 0)
        .map((channel) => {
          const best = channel.acestream_channels[0];
          return {
            key: `tv-${channel.id}`,
            label: channel.name,
            secondary: `Best stream: ${best.name} · ${describeOnline(best.is_online)}`,
            contentId: best.id,
          };
        });
    }
    return (streams.data?.items ?? []).map((stream) => ({
      key: `s-${stream.id}`,
      label: stream.name,
      secondary: `${stream.group || 'No group'} · ${describeOnline(stream.is_online)}`,
      contentId: stream.id,
    }));
  }, [mode, tv.data, streams.data]);

  const submit = async () => {
    if (!player || !selected) return;
    setError(null);
    try {
      await play.mutateAsync({ id: player.id, contentId: selected.contentId, title: selected.label });
      setSelected(null);
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? describeRemotePlayerError(err) : 'Could not reach the player.');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="channel-picker-title">
      <DialogTitle id="channel-picker-title">Send a channel to {player?.name ?? 'the player'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <ToggleButtonGroup
            exclusive
            size="small"
            value={mode}
            onChange={(_event, value: 'tv' | 'streams' | null) => {
              if (value) {
                setMode(value);
                setSelected(null);
              }
            }}
            aria-label="What to pick"
          >
            <ToggleButton value="tv">TV channels</ToggleButton>
            <ToggleButton value="streams">Streams</ToggleButton>
          </ToggleButtonGroup>
          <Autocomplete
            options={options}
            value={selected}
            onChange={(_event, value) => setSelected(value)}
            inputValue={search}
            onInputChange={(_event, value) => setSearch(value)}
            getOptionLabel={(option) => option.label}
            isOptionEqualToValue={(a, b) => a.key === b.key}
            loading={mode === 'tv' ? tv.isLoading : streams.isLoading}
            renderOption={(props, option) => {
              const { key: _key, ...liProps } = props as React.HTMLAttributes<HTMLLIElement> & { key?: React.Key };
              return (
                <li {...liProps} key={option.key}>
                  <Stack>
                    <Typography>{option.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {option.secondary}
                    </Typography>
                  </Stack>
                </li>
              );
            }}
            renderInput={(params) => <TextField {...params} label="Channel" placeholder="Type to search" />}
          />
          {error ? <Alert severity="error">{error}</Alert> : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" disabled={!selected || play.isPending} onClick={() => void submit()}>
          Send to {player?.name ?? 'player'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ChannelPickerDialog;
