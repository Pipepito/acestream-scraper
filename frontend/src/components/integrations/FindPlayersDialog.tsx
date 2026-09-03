import React, { useEffect, useState } from 'react';
import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useScanDefault, useScanRemotePlayers } from '../../hooks/useRemotePlayers';
import type { RemotePlayerKind, ScanHit } from '../../services/remotePlayerService';
import { getErrorMessage } from '../../utils/errorUtils';

export interface FindPlayersDialogProps {
  open: boolean;
  onClose: () => void;
  onAdd: (prefill: { host: string; port: number; kind: RemotePlayerKind }) => void;
}

const KIND_LABEL: Record<ScanHit['kind'], string> = { vlc: 'VLC', kodi: 'Kodi', unknown: 'Unknown' };

/** Scan one private network for VLC/Kodi web interfaces and add what answers. */
const FindPlayersDialog: React.FC<FindPlayersDialogProps> = ({ open, onClose, onAdd }) => {
  const { data: suggestion } = useScanDefault(open);
  const scan = useScanRemotePlayers();
  const [cidr, setCidr] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && suggestion?.cidr && !cidr) setCidr(suggestion.cidr);
  }, [open, suggestion, cidr]);

  const run = async () => {
    setError(null);
    try {
      await scan.mutateAsync({ cidr: cidr.trim(), ports: [8080] });
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const hits: ScanHit[] = scan.data?.hosts ?? [];
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm" aria-labelledby="find-players-title">
      <DialogTitle id="find-players-title">Find players</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Looks for VLC and Kodi web interfaces on port 8080. {suggestion?.hint}
          </Typography>
          <Stack direction="row" spacing={1}>
            <TextField
              label="Network"
              value={cidr}
              onChange={(event) => setCidr(event.target.value)}
              placeholder="192.168.1.0/24"
              fullWidth
              inputProps={{ 'aria-label': 'Network' }}
            />
            <Button variant="contained" onClick={() => void run()} disabled={!cidr.trim() || scan.isPending}>
              {scan.isPending ? <CircularProgress size={18} /> : 'Scan'}
            </Button>
          </Stack>
          {error ? <Alert severity="error">{error}</Alert> : null}
          {scan.data ? (
            hits.length === 0 ? (
              <Alert severity="info">
                Nothing answered on port 8080 across {scan.data.scanned} addresses. Turn on the web interface in VLC (Preferences ›
                Interface › Main interfaces › Web) or Kodi (Services › Control), then scan again.
              </Alert>
            ) : (
              <List dense>
                {hits.map((hit) => {
                  // Only a recognised player can be prefilled into the Add dialog.
                  const known: RemotePlayerKind | null = hit.kind === 'unknown' ? null : hit.kind;
                  return (
                    <ListItem
                      key={`${hit.host}:${hit.port}`}
                      secondaryAction={
                        known ? (
                          <Button size="small" onClick={() => onAdd({ host: hit.host, port: hit.port, kind: known })}>
                            Add
                          </Button>
                        ) : null
                      }
                    >
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center">
                            <span>
                              {hit.host}:{hit.port}
                            </span>
                            <Chip size="small" label={KIND_LABEL[hit.kind]} />
                          </Stack>
                        }
                        secondary={hit.hint}
                      />
                    </ListItem>
                  );
                })}
              </List>
            )
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default FindPlayersDialog;
