import { useUiText } from '../../i18n/useUiText';
import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { eventService, type SportingEvent } from '../../services/eventService';

export default function EventArtwork({ event }: { event: SportingEvent }) {
  const tUi = useUiText();
  const [enabled, setEnabled] = useState(false);
  const [url, setUrl] = useState('');
  const [decodeFailed, setDecodeFailed] = useState(false);
  const image = useQuery({ queryKey: ['event-artwork', event.id, event.revision], enabled, retry: false,
    queryFn: ({ signal }) => eventService.artwork(event.id, signal) });
  useEffect(() => {
    if (!image.data) return;
    const source = URL.createObjectURL(image.data);
    setUrl(source);
    setDecodeFailed(false);
    return () => URL.revokeObjectURL(source);
  }, [image.data]);
  if (!enabled) return <Button onClick={() => setEnabled(true)}>{tUi("Load event artwork")}</Button>;
  if (image.isError || decodeFailed) return <Alert severity="info" action={<Button onClick={() => { setDecodeFailed(false); setUrl(''); void image.refetch(); }}>{tUi("Retry artwork")}</Button>}>{tUi("Artwork is unavailable. Event details and broadcasts are still available.")}</Alert>;
  if (!url) return <CircularProgress size={24} aria-label={tUi("Loading event artwork")} />;
  return <Box component="img" src={url} alt={tUi("Artwork for {{value0}}", { value0: event.title })} onError={() => setDecodeFailed(true)} sx={{ width: '100%', maxHeight: 220, objectFit: 'contain' }} />;
}
