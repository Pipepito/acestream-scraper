import { uiText } from '../../i18n/text';
import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useRef, useState } from 'react';
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
import { useTVChannelPage } from '../../hooks/useTVChannels';
import { ApiError } from '../../services/apiErrors';
import type { RemotePlayer } from '../../services/remotePlayerService';
import { describePlaySent, describeRemotePlayerError, type PlayerNotify } from './playerCopy';

export interface ChannelPickerDialogProps {
  open: boolean;
  player: RemotePlayer | null;
  onClose: () => void;
  /** Where the send's outcome goes: the dialog closes, so it cannot show it itself. */
  notify: PlayerNotify;
}

interface PickerOption {
  key: string;
  label: string;
  secondary: string;
  contentId: string;
}

const describeOnline = (isOnline: boolean | null | undefined): string =>
  isOnline ? uiText("Online") : isOnline === false ? uiText("Offline") : uiText("Unchecked");

const useDebounced = (value: string, ms: number) => {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = window.setTimeout(() => setDebounced(value), ms);
    return () => window.clearTimeout(handle);
  }, [value, ms]);
  return debounced;
};

/** Pick a TV channel (best stream) or a raw stream and send it to a remote player. */
const ChannelPickerDialog: React.FC<ChannelPickerDialogProps> = ({ open, player, onClose, notify }) => {
  const tUi = useUiText();
  const [mode, setMode] = useState<'tv' | 'streams'>('tv');
  const [search, setSearch] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<PickerOption | null>(null);
  const [error, setError] = useState<unknown>(null);
  const pending = useRef(false);
  const debounced = useDebounced(query, 300);
  const tv = useTVChannelPage({ search: debounced, watchable: true, skip: page * 50, limit: 50 }, open && mode === 'tv');
  const streams = useAcestreamChannels(
    { search: debounced || undefined, is_active: true, page: page + 1, page_size: 50 },
    { enabled: open && mode === 'streams' }
  );
  const play = usePlayOnRemotePlayer();

  // The dialog stays mounted between openings; start each one empty.
  useEffect(() => {
    if (!open) return;
    setSearch('');
    setQuery('');
    setPage(0);
    setSelected(null);
    setError(null);
  }, [open]);

  const options: PickerOption[] = (() => {
    if (mode === 'tv') {
      return (tv.data?.items ?? [])
        .filter((channel) => channel.is_active && channel.acestream_channels.length > 0)
        .map((channel) => {
          const best = channel.acestream_channels[0];
          return {
            key: `tv-${channel.id}`,
            label: channel.name,
            secondary: uiText('Best stream: {{name}} · {{status}}', { name: best.name, status: describeOnline(best.is_online) }),
            contentId: best.id,
          };
        });
    }
    return (streams.data?.items ?? []).map((stream) => ({
      key: `s-${stream.id}`,
      label: stream.name,
      secondary: `${stream.group || tUi('No group')} · ${describeOnline(stream.is_online)}`,
      contentId: stream.id,
    }));
  })();
  const total = (mode === 'tv' ? tv.data?.total : streams.data?.total) ?? 0;
  const fetching = mode === 'tv' ? tv.isFetching : streams.isFetching;
  const loadingError = mode === 'tv' ? tv.isError : streams.isError;
  const shown = selected && !options.some(option => option.key === selected.key) ? [selected, ...options] : options;

  const submit = async () => {
    if (!player || !selected || pending.current) return;
    pending.current = true;
    setError(null);
    try {
      const result = await play.mutateAsync({ id: player.id, contentId: selected.contentId, title: selected.label });
      const sent = describePlaySent(selected.label, player.name, result.warnings);
      setSelected(null);
      onClose();
      notify(() => describePlaySent(selected.label, player.name, result.warnings).message, sent.severity);
    } catch (err) {
      setError(err);
    } finally { pending.current = false; }
  };

  return (
    <Dialog open={open} onClose={() => { if (!pending.current) onClose(); }} fullWidth maxWidth="sm" aria-labelledby="channel-picker-title">
      <DialogTitle id="channel-picker-title">{tUi("Send a channel to")}{' '}{player?.name ?? tUi('the player')}</DialogTitle>
      <DialogContent>
        <Stack component="fieldset" disabled={play.isPending} spacing={2} sx={{ mt: 1, p: 0, border: 0, minWidth: 0 }}>
          <ToggleButtonGroup
            exclusive
            size="small"
            value={mode}
            onChange={(_event, value: 'tv' | 'streams' | null) => {
              if (value) {
                setMode(value);
                setPage(0);
                setQuery('');
                setSearch('');
                setSelected(null);
              }
            }}
            aria-label={tUi("What to pick")}
          >
            <ToggleButton value="tv">{tUi("TV channels")}</ToggleButton>
            <ToggleButton value="streams">{tUi("Streams")}</ToggleButton>
          </ToggleButtonGroup>
          <Autocomplete
            options={shown}
            filterOptions={options => options}
            value={selected}
            onChange={(_event, value) => setSelected(value)}
            inputValue={search}
            onInputChange={(_event, value, reason) => { setSearch(value); if (reason === 'input' || reason === 'clear') { setQuery(value); setPage(0); } }}
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
            renderInput={(params) => <TextField {...params} label={tUi("Channel")} placeholder={tUi("Type to search")} />}
          />
          {loadingError ? <Alert severity="error" action={<Button onClick={() => void (mode === 'tv' ? tv.refetch() : streams.refetch())}>{tUi('Retry')}</Button>}>{tUi('Could not load channels. Try again.')}</Alert> : null}
          {total > 50 ? <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
            <Button disabled={page === 0 || fetching} onClick={() => setPage(value => value - 1)}>{tUi('Previous page')}</Button>
            <Typography variant="caption">{tUi('Page {{page}} of {{pages}}', { page: page + 1, pages: Math.ceil(total / 50) })}</Typography>
            <Button disabled={(page + 1) * 50 >= total || fetching} onClick={() => setPage(value => value + 1)}>{tUi('Next page')}</Button>
          </Stack> : null}
          {error !== null ? <Alert severity="error">{error instanceof ApiError ? describeRemotePlayerError(error) : tUi("Could not reach the player.")}</Alert> : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button disabled={play.isPending} onClick={() => { if (!pending.current) onClose(); }}>{tUi("Cancel")}</Button>
        <Button variant="contained" disabled={!selected || play.isPending} onClick={() => void submit()}>
          {tUi("Send to")}{' '}{player?.name ?? tUi('the player')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ChannelPickerDialog;
