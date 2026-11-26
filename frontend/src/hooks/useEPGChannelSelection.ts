import { getErrorMessage } from '../utils/errorUtils';
import { uiText } from '../i18n/text';
import React, { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { EPGChannel } from '../services/epgService';
import { tvChannelService } from '../services/tvChannelService';
import { TVChannel } from '../types/tvChannelTypes';
import { SnackbarNotify } from './useSnackbar';

interface UseEPGChannelSelectionParams {
  epgChannels: EPGChannel[];
  tvChannels: TVChannel[] | undefined;
  isLoadingTVChannelCatalog: boolean;
  tvChannelCatalogError: unknown;
  selectedSourceId: number | undefined;
  channelPage: number;
  channelPageSize: number;
  showSnackbar: SnackbarNotify;
}

/**
 * Hook owning EPG channel-inventory selection state and bulk TV-channel creation
 * for the EPG page.
 */
export const useEPGChannelSelection = ({
  epgChannels,
  tvChannels,
  isLoadingTVChannelCatalog,
  tvChannelCatalogError,
  selectedSourceId,
  channelPage,
  channelPageSize,
  showSnackbar
}: UseEPGChannelSelectionParams) => {
  const queryClient = useQueryClient();

  // State for EPG Channels selection
  const [selectedEPGChannelIds, setSelectedEPGChannelIds] = useState<number[]>([]);

  // EPG Channels selection handlers
  // A TV assignment to either member links the shared logical channel.
  const mappedEpgIds = useMemo(() => {
    if (!tvChannels) return new Set<string>();
    return new Set(tvChannels.filter((channel) => channel.epg_id).map((channel) => `${channel.epg_source_id ?? ''}:${channel.epg_id}`));
  }, [tvChannels]);

  const mappedChannelIds = useMemo(() => new Set(epgChannels.filter((channel) =>
    mappedEpgIds.has(`:${channel.channel_xml_id}`) ||
    (channel.sources?.map((source) => source.source_id) ?? [channel.epg_source_id])
      .some((id) => mappedEpgIds.has(`${id}:${channel.channel_xml_id}`))).map((channel) => channel.id)), [epgChannels, mappedEpgIds]);

  const visibleUnmappedChannelIds = useMemo(
    () => epgChannels.filter((channel) => !mappedChannelIds.has(channel.id)).map((channel) => channel.id),
    [epgChannels, mappedChannelIds]
  );

  const isTVChannelCatalogReady = !isLoadingTVChannelCatalog && !tvChannelCatalogError && Boolean(tvChannels);

  useEffect(() => {
    setSelectedEPGChannelIds([]);
  }, [selectedSourceId, channelPage, channelPageSize]);

  const isChannelMapped = (channel: EPGChannel) => mappedChannelIds.has(channel.id);

  const handleSelectAllChannels = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!isTVChannelCatalogReady) {
      return;
    }

    if (event.target.checked) {
      setSelectedEPGChannelIds(visibleUnmappedChannelIds);
    } else {
      setSelectedEPGChannelIds([]);
    }
  };

  const handleSelectChannel = (id: number) => {
    if (!isTVChannelCatalogReady) {
      return;
    }

    const channel = epgChannels?.find(c => c.id === id);
    if (!channel || isChannelMapped(channel)) return;
    setSelectedEPGChannelIds((prev) =>
      prev.includes(id) ? prev.filter((cid) => cid !== id) : [...prev, id]
    );
  };

  const handleBulkCreateTVChannels = async () => {
    if (!epgChannels) return;
    // Filter out already-mapped channels
    const unmappedIds = selectedEPGChannelIds.filter(id => {
      const channel = epgChannels.find(c => c.id === id);
      return channel && !isChannelMapped(channel);
    });
    if (unmappedIds.length === 0) {
      showSnackbar(() => (uiText("No unmapped EPG channels selected.")), 'warning');
      return;
    }
    try {
      const result = await tvChannelService.createFromEpg(unmappedIds);
      queryClient.invalidateQueries({ queryKey: ['tvChannels'] });
      queryClient.invalidateQueries({ queryKey: ['epg-channels'] });
      showSnackbar(
        () => (uiText("Created {{created}} TV channels, skipped {{skipped}}, auto-matched {{associated}} Acestream channels", { created: result.created_count, skipped: result.skipped_count, associated: result.associated_count })),
        'success'
      );
      setSelectedEPGChannelIds([]);
    } catch (error) {
      showSnackbar(() => (getErrorMessage(error)), 'error');
    }
  };

  return {
    selectedEPGChannelIds,
    visibleUnmappedChannelIds,
    isTVChannelCatalogReady,
    isChannelMapped,
    handleSelectAllChannels,
    handleSelectChannel,
    handleBulkCreateTVChannels
  };
};
