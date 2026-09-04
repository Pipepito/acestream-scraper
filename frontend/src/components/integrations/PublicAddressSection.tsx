import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { MEDIA_SERVERS_QUERY_KEY } from '../../hooks/useMediaServers';
import { PUBLIC_URL_QUERY_KEY, usePublicUrl } from '../../hooks/useSystemServices';
import { useTunerStatus } from '../../hooks/useTuner';
import { configService } from '../../services/configService';
import type { TunerDenial } from '../../services/tunerService';
import { getErrorMessage } from '../../utils/errorUtils';
import { formatRelativeTime } from '../../utils/format';

const SOURCE_LABEL = { setting: 'Setting', forwarded: 'Proxy headers', request: 'Request' } as const;

const WARNING_TEXT: Record<string, string> = {
  localhost:
    'This address only works from this machine. Jellyfin, Plex and players on other devices need the server’s network address, for example http://192.168.1.10:8000.',
  'docker-internal': 'This looks like a Docker-internal address that other devices cannot reach. Use the host’s LAN address instead.',
  unset: 'No public address is set, so links use whatever address your browser used. Set one if other devices should reach this server.',
  proxied:
    'The saved address differs from the one you are browsing from. Make sure /tuner/ is not behind proxy authentication (see the reverse-proxy guide).',
};

const ALLOWLIST_INEFFECTIVE =
  'This host hides real client addresses (Docker Desktop, rootless Docker, or IPv6 through docker-proxy); the private-network allowlist cannot tell your LAN from the internet. Publish the port IPv4-only, put a reverse proxy with allow/deny in front, or keep port 8000 off the internet.';

/** The most recent request the allowlist turned away, or null when there is none. */
const newestDenial = (denials: TunerDenial[]): TunerDenial | null =>
  denials.reduce<TunerDenial | null>((newest, denial) => (newest === null || denial.at > newest.at ? denial : newest), null);

/** Denials are stamped in POSIX seconds; formatRelativeTime wants an ISO string. */
const denialTime = (denial: TunerDenial): string => {
  const at = new Date(denial.at * 1000);
  return formatRelativeTime(Number.isNaN(at.getTime()) ? null : at.toISOString());
};

export interface PublicAddressSectionProps {
  notify: (message: string, severity: 'success' | 'error') => void;
}

/** Where tuners, remote players and copied links reach this server. */
const PublicAddressSection: React.FC<PublicAddressSectionProps> = ({ notify }) => {
  const queryClient = useQueryClient();
  const { data, isLoading } = usePublicUrl();
  const { data: tuner } = useTunerStatus();
  const denial = newestDenial(tuner?.recent_denials ?? []);
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const saved = data?.source === 'setting' ? data.url : '';

  useEffect(() => setValue(saved), [saved]);

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await configService.updatePublicBaseUrl(value.trim());
      notify(value.trim() ? 'Public address saved.' : 'Public address cleared.', 'success');
      await queryClient.invalidateQueries({ queryKey: PUBLIC_URL_QUERY_KEY });
      await queryClient.invalidateQueries({ queryKey: ['tuner'] });
      // The Plex cards paste absolute URLs built from this address; without
      // this they would keep the old ones until the next 30 s status poll.
      await queryClient.invalidateQueries({ queryKey: MEDIA_SERVERS_QUERY_KEY });
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Box id="public-address">
      <ContentSection
        title="Public address"
        description="The address other devices use to reach this server. It goes into tuner, player and copied links."
      >
        <Stack spacing={2}>
          <Typography variant="body2">
            Currently <strong>{isLoading ? '…' : data?.url}</strong>
            {data ? ` (${SOURCE_LABEL[data.source]})` : ''}
          </Typography>
          {(data?.warnings ?? []).map((warning) => (
            <Alert key={warning} severity="warning">
              {WARNING_TEXT[warning] ?? warning}
            </Alert>
          ))}
          {tuner?.warnings.includes('TUNER_ALLOWLIST_INEFFECTIVE') ? <Alert severity="warning">{ALLOWLIST_INEFFECTIVE}</Alert> : null}
          {denial ? (
            <Alert severity="warning">
              Requests from {denial.client_ip} were denied {denialTime(denial)} ({denial.path}); add its network to TUNER_ALLOWED_NETWORKS if it is
              yours.
            </Alert>
          ) : null}
          {tuner && tuner.overflow > 0 ? (
            <Alert severity="warning">
              Plex stops saving channel maps at roughly 450-480 channels (it depends on channel number and name length). {tuner.overflow} channels
              were left out; disable channels or lower the count.
            </Alert>
          ) : null}
          <Stack
            component="form"
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            alignItems={{ sm: 'flex-start' }}
            onSubmit={(event: React.FormEvent) => void save(event)}
            aria-label="Public address form"
          >
            <TextField
              size="small"
              fullWidth
              label="Public address"
              placeholder="http://192.168.1.10:8000"
              value={value}
              onChange={(event) => setValue(event.target.value)}
              inputProps={{ 'aria-label': 'Public address' }}
              helperText="Scheme and host, optionally a port. Leave empty to derive it from each request."
            />
            <Button type="submit" variant="contained" disabled={saving || value.trim() === saved}>
              Save
            </Button>
          </Stack>
        </Stack>
      </ContentSection>
    </Box>
  );
};

export default PublicAddressSection;
