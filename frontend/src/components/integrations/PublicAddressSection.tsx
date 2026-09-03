import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import ContentSection from '../layout/ContentSection';
import { PUBLIC_URL_QUERY_KEY, usePublicUrl } from '../../hooks/useSystemServices';
import { configService } from '../../services/configService';
import { getErrorMessage } from '../../utils/errorUtils';

const SOURCE_LABEL = { setting: 'Setting', forwarded: 'Proxy headers', request: 'Request' } as const;

const WARNING_TEXT: Record<string, string> = {
  localhost:
    'This address only works from this machine. Jellyfin, Plex and players on other devices need the server’s network address, for example http://192.168.1.10:8000.',
  'docker-internal': 'This looks like a Docker-internal address that other devices cannot reach. Use the host’s LAN address instead.',
  unset: 'No public address is set, so links use whatever address your browser used. Set one if other devices should reach this server.',
  proxied:
    'The saved address differs from the one you are browsing from. Make sure /tuner/ is not behind proxy authentication (see the reverse-proxy guide).',
};

export interface PublicAddressSectionProps {
  notify: (message: string, severity: 'success' | 'error') => void;
}

/** Where tuners, remote players and copied links reach this server. */
const PublicAddressSection: React.FC<PublicAddressSectionProps> = ({ notify }) => {
  const queryClient = useQueryClient();
  const { data, isLoading } = usePublicUrl();
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
