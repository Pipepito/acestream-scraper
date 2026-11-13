import { useUiText } from '../i18n/useUiText';
import GuideCoverage from '../components/GuideCoverage';
import React, { useState } from 'react';
import { Alert, Box, Collapse, Grid } from '@mui/material';
import StreamLinkFormatsSection from '../components/StreamLinkFormatsSection';
import PageHeader from '../components/layout/PageHeader';
import ContentSection from '../components/layout/ContentSection';
import PlaylistLinkPanel from '../components/playlist/PlaylistLinkPanel';
import PlaylistOptionsForm from '../components/playlist/PlaylistOptionsForm';
import { usePlaylistLink } from '../components/playlist/usePlaylistLink';

/** Build the M3U link, then download it or hand it to a player. */
const Playlist: React.FC = () => {
  const tUi = useUiText();
  const link = usePlaylistLink();
  const [formatsOpen, setFormatsOpen] = useState(false);
  const [formatNotice, setFormatNotice] = useState<{message: string | (() => string); severity: 'success' | 'error'} | null>(null);

  return (
    <Box>
      <PageHeader title={tUi("Playlist")} subtitle={tUi("One M3U link with your channels. Import it in your player and it stays up to date.")} />

      <ContentSection title={tUi("Programme guide")}><GuideCoverage /></ContentSection>
      <ContentSection title={tUi("Your playlist")}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <PlaylistOptionsForm link={link} formatsOpen={formatsOpen} onToggleFormats={() => setFormatsOpen((value) => !value)} />
          </Grid>
          <Grid item xs={12} md={5}>
            <PlaylistLinkPanel link={link} />
          </Grid>
        </Grid>
      </ContentSection>

      <Collapse in={formatsOpen} mountOnEnter unmountOnExit id="playlist-formats">
        <Alert severity="info" sx={{ mb: 2 }}>{tUi("Formats are shared with copied stream links and supported remote-player actions. Changing the default affects all links that use it.")}</Alert>
        {formatNotice ? <Alert severity={formatNotice.severity} onClose={() => setFormatNotice(null)}>{typeof formatNotice.message === 'function' ? formatNotice.message() : formatNotice.message}</Alert> : null}
        <StreamLinkFormatsSection notify={(message, severity) => setFormatNotice({ message, severity })} />
      </Collapse>
    </Box>
  );
};

export default Playlist;
