import { useUiText } from '../../i18n/useUiText';
import React from 'react';
import { Alert, Stack, Typography } from '@mui/material';
import ContentSection from '../layout/ContentSection';
import InlineStatusNotice from '../state/InlineStatusNotice';
import { useActiveStreams, usePlayerCapabilities } from '../../hooks/usePlayer';
import ActiveStreamsList from '../player/ActiveStreamsList';
import { getErrorMessage } from '../../utils/errorUtils';

/** ffmpeg availability and everything the server is streaming right now. */
const WebPlayerSection: React.FC = () => {
  const tUi = useUiText();
  const { data: caps, isError: capsFailed, error: capsError } = usePlayerCapabilities();
  const { data: active, isError: streamsFailed, error: streamsError } = useActiveStreams();
  const list = active?.streams ?? [];

  // Never state a capability we could not read: without an answer the line says
  // it is still checking, and a failed read says so with the reason.
  const ffmpegLine = (): React.ReactNode => {
    if (capsFailed) {
      return <InlineStatusNotice severity="error" title={tUi("Unable to check the web player")} description={getErrorMessage(capsError)} />;
    }
    if (!caps) {
      return (
        <Typography variant="body2" color="text.secondary">
          {tUi("Checking ffmpeg…")}</Typography>
      );
    }
    if (!caps.ffmpeg_available) {
      return (
        <Alert severity="warning">
          {tUi("ffmpeg is not available on this server, so channels cannot play in the browser. Set FFMPEG_BINARY_PATH or use the bundled image.")}</Alert>
      );
    }
    return (
      <Typography variant="body2" color="text.secondary">
        {tUi("ffmpeg")}{' '}{caps.ffmpeg_path ? tUi("at {{value0}}", { value0: caps.ffmpeg_path }) : tUi("ready")} {' '}{tUi("· up to")}{' '}{caps.max_sessions} {tUi("channels at once")}</Typography>
    );
  };

  return (
    <ContentSection
      title={tUi("Web player")}
      description={tUi("Channels play in the browser through a small server-side conversion (video copied, audio re-encoded). Media servers and remote players are relayed as they are.")}
    >
      <Stack spacing={1.5}>
        {ffmpegLine()}
        {streamsFailed ? (
          <InlineStatusNotice severity="error" title={tUi("Unable to load what is playing")} description={getErrorMessage(streamsError)} />
        ) : !active ? (
          <Typography role="status">{tUi("Loading playback…")}</Typography>
        ) : <ActiveStreamsList streams={list} showContentId />}

      </Stack>
    </ContentSection>
  );
};

export default WebPlayerSection;
