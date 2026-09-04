import React, { useEffect, useState } from 'react';
import { Box, Button, Chip, Grid, IconButton, Paper, Slider, Stack, Tooltip, Typography, useTheme } from '@mui/material';
import PauseRoundedIcon from '@mui/icons-material/PauseRounded';
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded';
import StopRoundedIcon from '@mui/icons-material/StopRounded';
import ContentSection from '../layout/ContentSection';
import RowActionsMenu from '../RowActionsMenu';
import { useConfirm } from '../ConfirmDialog';
import EmptyState from '../state/EmptyState';
import InlineStatusNotice from '../state/InlineStatusNotice';
import {
  useDeleteRemotePlayer,
  useRemotePlayerCommand,
  useRemotePlayerStatus,
  useRemotePlayers,
} from '../../hooks/useRemotePlayers';
import { ApiError } from '../../services/apiErrors';
import { remotePlayerService, type RemotePlayer, type RemotePlayerKind } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';
import { describeRemotePlayerError, type PlayerNotify } from '../player/playerCopy';
import ChannelPickerDialog from '../player/ChannelPickerDialog';
import FindPlayersDialog from './FindPlayersDialog';
import RemotePlayerDialog from './RemotePlayerDialog';

export interface RemotePlayersSectionProps {
  notify: PlayerNotify;
}

const KIND_LABEL: Record<RemotePlayerKind, string> = { vlc: 'VLC', kodi: 'Kodi' };

const formatClock = (seconds: number | null | undefined): string => {
  if (seconds === null || seconds === undefined) return '';
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}:${String(rest).padStart(2, '0')}`;
};

interface PlayerCardProps {
  player: RemotePlayer;
  onEdit: () => void;
  onDelete: () => void;
  onSend: () => void;
  onTest: () => void;
  notify: RemotePlayersSectionProps['notify'];
}

const PlayerCard: React.FC<PlayerCardProps> = ({ player, onEdit, onDelete, onSend, onTest, notify }) => {
  const theme = useTheme();
  const { data: status, error, dataUpdatedAt } = useRemotePlayerStatus(player.id);
  const command = useRemotePlayerCommand();
  // While the user drags (and until a status read taken after the command lands),
  // the slider follows the finger instead of the 5 s poll.
  const [volumeDraft, setVolumeDraft] = useState<number | null>(null);
  const [volumeSentAt, setVolumeSentAt] = useState<number | null>(null);
  const volumePct = volumeDraft ?? status?.volume_pct ?? 0;

  useEffect(() => {
    if (volumeSentAt !== null && dataUpdatedAt > volumeSentAt) {
      setVolumeDraft(null);
      setVolumeSentAt(null);
    }
  }, [dataUpdatedAt, volumeSentAt]);

  const run = async (cmd: 'pause' | 'resume' | 'stop' | 'volume', value?: number) => {
    try {
      await command.mutateAsync({ id: player.id, command: cmd, value });
    } catch (err) {
      notify(err instanceof ApiError ? describeRemotePlayerError(err) : getErrorMessage(err), 'error');
    }
  };

  const sendVolume = async (value: number) => {
    setVolumeDraft(value);
    setVolumeSentAt(null);
    await run('volume', value);
    setVolumeSentAt(Date.now());
  };

  const statusText = error
    ? error instanceof ApiError
      ? describeRemotePlayerError(error)
      : 'Unreachable'
    : status
      ? status.state === 'stopped'
        ? 'Idle'
        : `${status.state === 'playing' ? 'Playing' : 'Paused'}${status.title ? ` · ${status.title}` : ''}${
            status.position_s !== null ? ` · ${formatClock(status.position_s)}` : ''
          }`
      : 'Checking…';
  const tone = error ? 'error' : status?.state === 'playing' ? 'success' : 'default';

  return (
    <Paper
      variant="outlined"
      role="group"
      aria-label={`Player ${player.name}`}
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 1,
        borderColor: theme.appTokens.surface.border,
        backgroundColor: theme.appTokens.surface.raised,
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
        <Box sx={{ minWidth: 0 }}>
          <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
            {player.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {player.host}:{player.port}
          </Typography>
        </Box>
        <Chip size="small" label={KIND_LABEL[player.kind]} />
      </Stack>
      <Typography
        variant="body2"
        role="status"
        color={tone === 'error' ? 'error.main' : tone === 'success' ? 'success.main' : 'text.secondary'}
      >
        {statusText}
      </Typography>
      <Stack direction="row" spacing={1} alignItems="center">
        {status?.state === 'playing' ? (
          <Tooltip title="Pause">
            <IconButton size="small" aria-label={`Pause ${player.name}`} onClick={() => void run('pause')}>
              <PauseRoundedIcon />
            </IconButton>
          </Tooltip>
        ) : (
          <Tooltip title="Resume">
            <span>
              <IconButton
                size="small"
                aria-label={`Resume ${player.name}`}
                disabled={!status || status.state === 'stopped'}
                onClick={() => void run('resume')}
              >
                <PlayArrowRoundedIcon />
              </IconButton>
            </span>
          </Tooltip>
        )}
        <Tooltip title="Stop">
          <span>
            <IconButton
              size="small"
              aria-label={`Stop ${player.name}`}
              disabled={!status || status.state === 'stopped'}
              onClick={() => void run('stop')}
            >
              <StopRoundedIcon />
            </IconButton>
          </span>
        </Tooltip>
        <Slider
          size="small"
          aria-label={`Volume ${player.name}`}
          value={volumePct}
          min={0}
          max={200}
          sx={{ mx: 1, flex: 1 }}
          disabled={!status}
          onChange={(_event, value) => setVolumeDraft(Array.isArray(value) ? value[0] : value)}
          onChangeCommitted={(_event, value) => void sendVolume(Array.isArray(value) ? value[0] : value)}
        />
        <RowActionsMenu
          label={`More actions for ${player.name}`}
          actions={[
            { label: 'Send channel…', onClick: onSend },
            { label: 'Edit', onClick: onEdit },
            { label: 'Test connection', onClick: onTest },
            { label: 'Delete', danger: true, onClick: onDelete },
          ]}
        />
      </Stack>
    </Paper>
  );
};

/** Saved VLC/Kodi players with live status and transport controls. */
const RemotePlayersSection: React.FC<RemotePlayersSectionProps> = ({ notify }) => {
  const { data: players = [], isLoading, isError, error, refetch } = useRemotePlayers();
  const remove = useDeleteRemotePlayer();
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [editing, setEditing] = useState<RemotePlayer | null>(null);
  const [adding, setAdding] = useState(false);
  const [prefill, setPrefill] = useState<{ host: string; port: number; kind: RemotePlayerKind } | null>(null);
  const [finding, setFinding] = useState(false);
  const [sending, setSending] = useState<RemotePlayer | null>(null);

  const handleDelete = async (player: RemotePlayer) => {
    const ok = await confirm({
      title: `Delete ${player.name}?`,
      body: 'The player is removed from this list. Nothing changes on the player itself.',
      confirmLabel: 'Delete',
      danger: true,
    });
    if (!ok) return;
    try {
      await remove.mutateAsync(player.id);
      notify(`Deleted ${player.name}.`, 'success');
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    }
  };

  const handleTest = async (player: RemotePlayer) => {
    try {
      const probe = await remotePlayerService.testSaved(player.id);
      const ok = probe.reachable && probe.authenticated;
      notify(ok ? `${player.name} answered${probe.version ? ` (version ${probe.version})` : ''}.` : probe.hint ?? probe.message, ok ? 'success' : 'error');
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    }
  };

  return (
    <ContentSection
      title="Remote players"
      description="VLC or Kodi on your network. Send any channel there and control playback from here."
      actions={
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" size="small" onClick={() => setFinding(true)}>
            Find players
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={() => {
              setPrefill(null);
              setAdding(true);
            }}
          >
            Add player
          </Button>
        </Stack>
      }
    >
      {isError ? (
        <InlineStatusNotice
          severity="error"
          title="Unable to load players"
          description={getErrorMessage(error)}
          action={
            <Button variant="outlined" size="small" onClick={() => void refetch()}>
              Try again
            </Button>
          }
        />
      ) : isLoading ? (
        <Typography variant="body2">Loading players…</Typography>
      ) : players.length === 0 ? (
        <EmptyState title="No players yet" description="Add VLC or Kodi from a device on this network, or scan for them." />
      ) : (
        <Grid container spacing={2}>
          {players.map((player) => (
            <Grid item xs={12} md={6} lg={4} key={player.id}>
              <PlayerCard
                player={player}
                notify={notify}
                onEdit={() => setEditing(player)}
                onDelete={() => void handleDelete(player)}
                onSend={() => setSending(player)}
                onTest={() => void handleTest(player)}
              />
            </Grid>
          ))}
        </Grid>
      )}
      <RemotePlayerDialog
        open={adding || editing !== null}
        player={editing}
        prefill={prefill}
        onClose={() => {
          setAdding(false);
          setEditing(null);
        }}
        notify={notify}
      />
      <FindPlayersDialog
        open={finding}
        onClose={() => setFinding(false)}
        onAdd={(hit) => {
          setFinding(false);
          setPrefill(hit);
          setAdding(true);
        }}
      />
      <ChannelPickerDialog open={sending !== null} player={sending} onClose={() => setSending(null)} notify={notify} />
      {confirmDialog}
    </ContentSection>
  );
};

export default RemotePlayersSection;
