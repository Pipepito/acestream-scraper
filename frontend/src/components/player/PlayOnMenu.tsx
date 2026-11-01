import React, { useState } from 'react';
import { Alert, Button, Divider, ListItemIcon, ListItemText, Menu, MenuItem, Snackbar } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import CastRoundedIcon from '@mui/icons-material/CastRounded';
import { Link as RouterLink } from 'react-router-dom';
import { usePlayOnRemotePlayer, useRemotePlayers } from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import { describePlaySent, describeRemotePlayerError, type PlayerNotify } from './playerCopy';
import { useAccess } from '../access/AccessContext';
import { castService } from '../../services/castService';
import { getAccessErrorMessage } from '../../services/accessErrors';
import { CastDialog } from './CastControls';

export interface PlayOnMenuProps {
  contentId: string;
  title: string;
  label?: string;
  /** Rendered as a button that opens the menu (default). */
  variant?: 'button';
  onDone?: () => void;
  /**
   * Where feedback goes. Callers that close their dialog in `onDone` must pass this:
   * closing unmounts the menu's own snackbar before the confirmation can be read.
   */
  notify?: PlayerNotify;
}

const KIND_LABEL: Record<string, string> = { vlc: 'VLC', vlc_android: 'VLC Android', kodi: 'Kodi' };

/** Send directly to a receiver; opening this menu never starts browser playback. */
const PlayOnMenu: React.FC<PlayOnMenuProps> = ({ contentId, title, label, onDone, notify }) => {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [notice, setNotice] = useState<{ message: string; severity: 'success' | 'warning' | 'error' } | null>(null);
  const { data: players = [], isLoading } = useRemotePlayers();
  const play = usePlayOnRemotePlayer();
  const access = useAccess();
  const cache = useQueryClient();
  const [casting, setCasting] = useState(false);
  const [finding, setFinding] = useState(false);
  const [castOptions, setCastOptions] = useState(false);
  const canCast = Boolean(access?.status.mode === 'open' || access?.status.user?.administrator ||
    (access?.status.permissions?.includes('cast_server') && access.status.permissions?.includes('live')));
  const capabilities = useQuery({ queryKey: ['cast-capabilities'], queryFn: castService.capabilities, enabled: Boolean(anchor) && canCast, retry: false });
  const serverAllowed = canCast && capabilities.data?.server_devices;
  const devices = useQuery({ queryKey: ['cast-devices'], queryFn: castService.devices, enabled: Boolean(anchor) && Boolean(serverAllowed), refetchInterval: anchor && serverAllowed ? 3000 : false, retry: false });

  const report: PlayerNotify = (message, severity) => {
    if (notify) notify(message, severity);
    else setNotice({ message, severity });
  };

  const send = async (id: number, name: string) => {
    setAnchor(null);
    try {
      const result = await play.mutateAsync({ id, contentId, title });
      const sent = describePlaySent(title, name, result.warnings);
      report(sent.message, sent.severity);
      onDone?.();
    } catch (err) {
      report(err instanceof ApiError ? describeRemotePlayerError(err) : 'Could not reach the player.', 'error');
    }
  };

  const sendToTv = async (id: string, name: string) => {
    setAnchor(null);
    setCasting(true);
    try {
      await castService.start({ content_id: contentId, device_id: id, audio_index: null, subtitle_index: null, compatibility: false, replace: false });
      void cache.invalidateQueries({ queryKey: ['cast-sessions'] });
      report(`Casting ${title} to ${name}.`, 'success');
      onDone?.();
    } catch (error) {
      report(getAccessErrorMessage(error), 'error');
      // The shared dialog provides explicit replacement confirmation and
      // compatibility choices. Never retry a failed start with replace=true.
      setCastOptions(true);
    } finally { setCasting(false); }
  };

  const findTvs = async () => {
    setFinding(true);
    try {
      await cache.cancelQueries({ queryKey: ['cast-devices'] });
      const found = await castService.discover();
      cache.setQueryData(['cast-devices'], found);
      if (!found.length) report('No TVs found. Check TV casting settings and the server’s network connection.', 'warning');
    } catch (error) { report(getAccessErrorMessage(error), 'error'); }
    finally { setFinding(false); }
  };

  return (
    <>
      <Button
        startIcon={<CastRoundedIcon />}
        onClick={(event) => setAnchor(event.currentTarget)}
        aria-haspopup="menu"
        aria-label={label ? `${label} ${title}` : undefined}
        aria-expanded={Boolean(anchor)}
        disabled={play.isPending || casting}
      >
        {casting ? 'Starting cast…' : label ?? 'Play on…'}
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)} slotProps={{ paper: { sx: { maxWidth: 'calc(100vw - 32px)', '& .MuiListItemText-root': { whiteSpace: 'normal', overflowWrap: 'anywhere' } } } }}>
        {isLoading ? <MenuItem disabled>Loading players…</MenuItem> : players.length === 0
          ? (
              <MenuItem component={RouterLink} to="/integrations/remote-players" onClick={() => setAnchor(null)}>
                <ListItemText primary="Add a player" secondary="VLC or Kodi on your network, under Integrations" />
              </MenuItem>
            )
          : players.map((player) => (
              <MenuItem key={player.id} onClick={() => void send(player.id, player.name)}>
                <ListItemIcon>
                  <CastRoundedIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText>{`${player.name} (${KIND_LABEL[player.kind] ?? player.kind})`}</ListItemText>
              </MenuItem>
            ))}
        {canCast ? <Divider /> : null}
        {canCast && capabilities.isFetching && !capabilities.data ? <MenuItem disabled>Checking TV casting…</MenuItem> : null}
        {serverAllowed ? devices.data?.map(tv => <MenuItem key={tv.id} onClick={() => void sendToTv(tv.id, tv.name)} disabled={casting || !capabilities.data?.media_url_configured}>
          <ListItemIcon><CastRoundedIcon fontSize="small" /></ListItemIcon>
          <ListItemText primary={tv.name} secondary="Google Cast TV" />
        </MenuItem>) : null}
        {serverAllowed ? <MenuItem disabled={finding} onClick={() => void findTvs()}>{finding ? 'Finding TVs…' : 'Find TVs'}</MenuItem> : null}
        {canCast ? <MenuItem onClick={() => { setAnchor(null); setCastOptions(true); }}>Casting options and controls…</MenuItem> : null}
        {canCast && (capabilities.isError || devices.isError) ? <MenuItem disabled>Could not load TVs. Open casting options to retry.</MenuItem> : null}
        {canCast && capabilities.data && !serverAllowed ? <MenuItem component={RouterLink} to="/integrations/tv-casting" onClick={() => setAnchor(null)}><ListItemText primary="Check TV casting access" secondary={capabilities.data.message} /></MenuItem> : null}
      </Menu>
      {canCast && castOptions ? <CastDialog contentId={contentId} audioIndex={null} subtitleIndex={null} open onClose={() => setCastOptions(false)} /> : null}
      {notify ? null : (
        <Snackbar open={notice !== null} autoHideDuration={5000} onClose={() => setNotice(null)}>
          <Alert severity={notice?.severity ?? 'success'} onClose={() => setNotice(null)}>
            {notice?.message}
          </Alert>
        </Snackbar>
      )}
    </>
  );
};

export default PlayOnMenu;
