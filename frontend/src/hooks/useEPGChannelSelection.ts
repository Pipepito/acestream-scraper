import React, { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from 'react-query';
import { EPGChannel } from '../services/epgService';
import { tvChannelService } from '../services/tvChannelService';
import { TVChannel } from '../types/tvChannelTypes';
import { SnackbarSeverity } from './useSnackbar';

interface UseEPGChannelSelectionParams {
  epgChannels: EPGChannel[];
  tvChannels: TVChannel[] | undefined;
  isLoadingTVChannelCatalog: boolean;
  tvChannelCatalogError: unknown;
  selectedSourceId: number | undefined;
  channelPage: number;
  channelPageSize: number;
  showSnackbar: (message: string, severity: SnackbarSeverity) => void;
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
  // Build a set of mapped EPG XML IDs (or channel_xml_id)
  const mappedEpgXmlIds = useMemo(() => {
    if (!tvChannels) return new Set<string>();
    return new Set(tvChannels.filter((channel: any) => channel.epg_id).map((channel: any) => channel.epg_id));
  }, [tvChannels]);

  const visibleUnmappedChannelIds = useMemo(
    () => epgChannels.filter((channel) => !mappedEpgXmlIds.has(channel.channel_xml_id)).map((channel) => channel.id),
    [epgChannels, mappedEpgXmlIds]
  );

  const isTVChannelCatalogReady = !isLoadingTVChannelCatalog && !tvChannelCatalogError && Boolean(tvChannels);

  useEffect(() => {
    setSelectedEPGChannelIds([]);
  }, [selectedSourceId, channelPage, channelPageSize]);

  const isChannelMapped = (channel: EPGChannel) => mappedEpgXmlIds.has(channel.channel_xml_id);

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
      showSnackbar('No unmapped EPG channels selected.', 'warning');
      return;
    }
    try {
      const result = await tvChannelService.createFromEpg(unmappedIds);
      queryClient.invalidateQueries('tvChannels');
      queryClient.invalidateQueries('epg-channels');
      showSnackbar(
        `Created ${result.created_count} TV channels, skipped ${result.skipped_count}, auto-matched ${result.associated_count} Acestream channels`,
        'success'
      );
      setSelectedEPGChannelIds([]);
    } catch (error) {
      showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
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
