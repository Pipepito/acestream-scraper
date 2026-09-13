import React, { useState } from 'react';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import { systemService } from '../services/systemService';

export default function DiagnosticsDownload() {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const download = async () => {
    setBusy(true);
    setFailed(false);
    try {
      await systemService.downloadDiagnostics();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Box>
      <Button variant="outlined" disabled={busy} onClick={() => void download()}>
        {busy ? 'Gathering diagnostics…' : 'Download diagnostics'}
      </Button>
      {failed ? <Alert severity="error" sx={{ mt: 1 }}>Could not download diagnostics. Try again.</Alert> : null}
    </Box>
  );
}
