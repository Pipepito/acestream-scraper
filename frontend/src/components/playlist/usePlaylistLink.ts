import { uiText } from '../../i18n/text';
import { useEffect, useState, type Dispatch, type SetStateAction } from 'react';
import { useChannelGroups, usePlaylistChannelSummary } from '../../hooks/usePlaylists';
import { useBaseUrls } from '../../hooks/useBaseUrls';
import { usePublicUrl } from '../../hooks/useSystemServices';
import { PlaylistFilters, playlistService, getAbsolutePlaylistUrl, buildPublicUrl } from '../../services/playlistService';
import type { StreamBaseUrl } from '../../services/baseUrlService';
import { useAccess } from '../access/AccessContext';
import { accessService } from '../../services/accessService';

export type BaseUrlChoice = number | '' | 'tv-relay';

export interface PlaylistFormat { name: string; pattern: string }

/** Everything the playlist options form and link panel share, on the page and in the dialog. */
export interface PlaylistLink {
  managed: boolean;
  filters: PlaylistFilters;
  setFilters: Dispatch<SetStateAction<PlaylistFilters>>;
  search: string;
  setSearch: (value: string) => void;
  selectedBaseUrlId: BaseUrlChoice;
  setSelectedBaseUrlId: (value: BaseUrlChoice) => void;
  namedBaseUrls: StreamBaseUrl[];
  loadingBaseUrls: boolean;
  baseUrlsError: boolean;
  channelGroups: string[];
  loadingGroups: boolean;
  selectedFormat: PlaylistFormat | undefined;
  isRelay: boolean;
  playlistUrl: string;
  absolutePlaylistUrl: string;
  playbackToken: string;
  creatingLink: boolean;
  linkError: string;
  createLink: () => Promise<void>;
  onlineHelp: string;
}

export function usePlaylistLink(): PlaylistLink {
  const managed = useAccess()?.status.mode === 'accounts';
  const [playbackToken, setPlaybackToken] = useState('');
  const [creatingLink, setCreatingLink] = useState(false);
  const [linkError, setLinkError] = useState('');
  const [filters, setFilters] = useState<PlaylistFilters>({ only_online: false, include_unassigned: false, include_groups: [], exclude_groups: [] });
  const [search, setSearch] = useState('');
  const [selectedBaseUrlId, setSelectedBaseUrlId] = useState<BaseUrlChoice>('');

  const { data: channelGroups = [], isLoading: loadingGroups } = useChannelGroups();
  const { data: namedBaseUrls = [], isLoading: loadingBaseUrls, isError: baseUrlsError } = useBaseUrls();
  const { data: publicUrl } = usePublicUrl();
  const { data: summary } = usePlaylistChannelSummary();

  useEffect(() => {
    if (!loadingBaseUrls && !baseUrlsError && selectedBaseUrlId !== '' && selectedBaseUrlId !== 'tv-relay' && !namedBaseUrls.some(entry => entry.id === selectedBaseUrlId)) setSelectedBaseUrlId('');
  }, [namedBaseUrls, loadingBaseUrls, baseUrlsError, selectedBaseUrlId]);
  const relayPattern = buildPublicUrl('/tuner/channel/{tv_channel_id}.ts', publicUrl?.url).replace('%7Btv_channel_id%7D', '{tv_channel_id}');
  const selectedFormat: PlaylistFormat | undefined = selectedBaseUrlId === 'tv-relay'
    ? { name: 'TV channel relay (automatic failover)', pattern: relayPattern }
    : namedBaseUrls.find(entry => selectedBaseUrlId === '' ? entry.is_default : entry.id === selectedBaseUrlId);

  const isRelay = managed || Boolean(selectedFormat?.pattern?.includes('{tv_channel_id}'));
  const effectiveFilters: PlaylistFilters = {
    ...filters,
    search: search || undefined,
    include_unassigned: !filters.favorites_only && filters.include_unassigned,
    per_source: isRelay && filters.per_source ? true : undefined,
    base_url_id: typeof selectedBaseUrlId === 'number' ? selectedBaseUrlId : undefined,
    base_url: selectedBaseUrlId === 'tv-relay' ? relayPattern : undefined,
  };
  const appendCredential = (url: string) => playbackToken ? `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(playbackToken)}` : url;
  const playlistUrl = appendCredential(playlistService.getPlaylistDownloadUrl(effectiveFilters));
  const absolutePlaylistUrl = appendCredential(getAbsolutePlaylistUrl(effectiveFilters, publicUrl?.url));
  const createLink = async () => {
    setCreatingLink(true); setLinkError('');
    try { const link = await accessService.playlistLink(); setPlaybackToken(new URL(link.url).searchParams.get('token') ?? ''); }
    catch { setLinkError('Could not create a playback credential. Check Settings → Access.'); }
    finally { setCreatingLink(false); }
  };
  const onlineHelp = summary
    ? `${summary.online} of ${summary.total_channels} channels are online right now`
    : uiText("Channels the last status check found online");

  return { managed, filters, setFilters, search, setSearch, selectedBaseUrlId, setSelectedBaseUrlId, namedBaseUrls, loadingBaseUrls,
    baseUrlsError: Boolean(baseUrlsError), channelGroups, loadingGroups, selectedFormat, isRelay, playlistUrl, absolutePlaylistUrl,
    playbackToken, creatingLink, linkError, createLink, onlineHelp };
}
