import { Visibility as VisibilityIcon,VisibilityOff as VisibilityOffIcon } from '@mui/icons-material';
import {
Alert,
Button,
IconButton,
InputAdornment,
Stack,
TextField
} from '@mui/material';
import React,{ useState } from 'react';
import { useUiText } from '../../i18n/useUiText';
import { getApiToken,isApiTokenRequired,clearApiToken as removeStoredApiToken,resetApiTokenRequired,setApiToken as storeApiToken } from '../../services/apiToken';
import { useAccess } from '../access/AccessContext';
import AccessSettings from '../access/AccessSettings';
import ContentSection from '../layout/ContentSection';

import { useUnsavedChanges } from '../UnsavedChanges';
type FeedbackSeverity = 'success' | 'error';
type Notify = (message: string, severity: FeedbackSeverity) => void;

export default function AccessSection({ notify }: { notify: Notify }) {
  const tUi = useUiText();
  const access = useAccess();
  const [apiTokenInput, setApiTokenInput] = useState<string>(() => getApiToken() ?? '');
  const [savedToken, setSavedToken] = useState(apiTokenInput);
  const [showApiToken, setShowApiToken] = useState(false);
  const [apiTokenRequired, setApiTokenRequired] = useState<boolean>(() => isApiTokenRequired());
  useUnsavedChanges(apiTokenInput !== savedToken);
  const handleApiTokenSave = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = apiTokenInput.trim();
    if (!trimmed) return;
    storeApiToken(trimmed);
    setApiTokenInput(trimmed); setSavedToken(trimmed);
    resetApiTokenRequired();
    setApiTokenRequired(false);
    notify(tUi("API token saved. It will be sent with future API requests."), 'success');
  };

  const handleApiTokenClear = () => {
    removeStoredApiToken();
    setApiTokenInput(''); setSavedToken('');
    resetApiTokenRequired();
    setApiTokenRequired(false);
    notify(tUi("API token cleared"), 'success');
  };

  return <><AccessSettings />
      {access?.status.mode !== 'accounts' ? <ContentSection title={tUi("Legacy API access")} description={tUi("Only needed when the server sets API_TOKEN. The token is stored in this browser and sent with every request.")}>
        <Stack spacing={2} sx={{ maxWidth: 520 }}>
          {apiTokenRequired ? (
            <Alert severity="warning">{tUi("The server rejected a request because a valid token is missing. Enter the token below to restore access.")}</Alert>
          ) : null}
          <form onSubmit={handleApiTokenSave}>
            <Stack spacing={2}>
              <TextField
                id="api-token"
                label={tUi("API token")}
                size="small"
                type={showApiToken ? 'text' : 'password'}
                fullWidth
                value={apiTokenInput}
                onChange={(e) => setApiTokenInput(e.target.value)}
                autoComplete="off"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton aria-label={showApiToken ? tUi("Hide API token") : tUi("Show API token")} onClick={() => setShowApiToken((current) => !current)} edge="end" size="small">
                        {showApiToken ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              <Stack direction="row" spacing={1}>
                <Button type="submit" variant="contained" size="small" disabled={!apiTokenInput.trim()}>
                  {tUi("Save token")}</Button>
                <Button variant="outlined" color="inherit" size="small" onClick={handleApiTokenClear}>
                  {tUi("Clear token")}</Button>
              </Stack>
            </Stack>
          </form>
        </Stack>
      </ContentSection> : null}

</>;
}
