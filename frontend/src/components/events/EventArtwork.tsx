import React, { useEffect, useState } from 'react';
import { Alert, Box, Button, CircularProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { eventService, type SportingEvent } from '../../services/eventService';

export default function EventArtwork({ event }: { event: SportingEvent }) {
  const [enabled, setEnabled] = useState(false);
  const [url, setUrl] = useState('');
  const image = useQuery({ queryKey: ['event-artwork', event.id, event.revision], enabled, retry: false,
    queryFn: ({ signal }) => eventService.artwork(event.id, signal) });
  useEffect(() => {
    if (!image.data) return;
    const source = URL.createObjectURL(image.data);
    setUrl(source);
    return () => URL.revokeObjectURL(source);
  }, [image.data]);
  if (!enabled) return <Button onClick={() => setEnabled(true)}>Load event artwork</Button>;
  if (image.isError) return <Alert severity="info" action={<Button onClick={() => void image.refetch()}>Retry artwork</Button>}>Artwork is unavailable. Event details and broadcasts are still available.</Alert>;
  if (!url) return <CircularProgress size={24} aria-label="Loading event artwork" />;
  return <Box component="img" src={url} alt={`Artwork for ${event.title}`} sx={{ width: '100%', maxHeight: 220, objectFit: 'contain' }} />;
}
