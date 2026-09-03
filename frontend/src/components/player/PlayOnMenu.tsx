import React, { useState } from 'react';
import { Alert, Button, ListItemIcon, ListItemText, Menu, MenuItem, Snackbar } from '@mui/material';
import CastRoundedIcon from '@mui/icons-material/CastRounded';
import { Link as RouterLink } from 'react-router-dom';
import { usePlayOnRemotePlayer, useRemotePlayers } from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import { describeRemotePlayerError } from './playerCopy';

export interface PlayOnMenuProps {
  contentId: string;
  title: string;
  /** Rendered as a button that opens the menu (default). */
  variant?: 'button';
  onDone?: () => void;
  /**
   * Where feedback goes. Callers that close their dialog in `onDone` must pass this:
   * closing unmounts the menu's own snackbar before the confirmation can be read.
   */
  notify?: (message: string, severity: 'success' | 'error') => void;
}

const KIND_LABEL: Record<string, string> = { vlc: 'VLC', kodi: 'Kodi' };

/** "Play on…": send a channel to a saved VLC/Kodi player. */
const PlayOnMenu: React.FC<PlayOnMenuProps> = ({ contentId, title, onDone, notify }) => {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [notice, setNotice] = useState<{ message: string; severity: 'success' | 'error' } | null>(null);
  const { data: players = [], isLoading } = useRemotePlayers();
  const play = usePlayOnRemotePlayer();

  const report = (message: string, severity: 'success' | 'error') => {
    if (notify) notify(message, severity);
    else setNotice({ message, severity });
  };

  const send = async (id: number, name: string) => {
    setAnchor(null);
    try {
      await play.mutateAsync({ id, contentId, title });
      report(`Sent ${title} to ${name}.`, 'success');
      onDone?.();
    } catch (err) {
      report(err instanceof ApiError ? describeRemotePlayerError(err) : 'Could not reach the player.', 'error');
    }
  };

  return (
    <>
      <Button
        startIcon={<CastRoundedIcon />}
        onClick={(event) => setAnchor(event.currentTarget)}
        aria-haspopup="menu"
        aria-expanded={Boolean(anchor)}
        disabled={isLoading || play.isPending}
      >
        Play on…
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
        {players.length === 0
          ? (
              <MenuItem component={RouterLink} to="/integrations" onClick={() => setAnchor(null)}>
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
      </Menu>
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
