import type { APIRequestContext, APIResponse } from '@playwright/test';
import { pollUntil } from './stack';

/* ---------- response shapes (subset of the backend DTOs the suite relies on) ---------- */
export interface HealthResponse {
  status: 'healthy' | 'degraded' | string;
  acestream: { status: string; message?: string; details?: string };
  database?: { status: string };
  version?: string;
}
export interface UrlResponse {
  id: number;
  url: string;
  url_type: string;
  status: string | null;
  last_processed: string | null;
  last_scraped: string | null;
  error_count: number;
  last_error: string | null;
  enabled: boolean;
  scrape_bare_ids: boolean;
  channels_found: number;
}
export interface AcestreamChannel {
  id: string;
  name: string;
  source_url: string | null;
  group: string | null;
  logo: string | null;
  tvg_id: string | null;
  tvg_name: string | null;
  is_active: boolean;
  is_online: boolean | null;
  last_checked: string | null;
  check_error: string | null;
  tv_channel_id: number | null;
  tv_channel_name?: string | null;
}
export interface Paged<T> {
  items: T[];
  total: number;
}
export interface TvChannel {
  id: number;
  name: string;
  category: string | null;
  epg_id: string | null;
  epg_source_id: number | null;
  is_active: boolean;
  is_favorite: boolean;
  channel_number: number | null;
  website?: string | null;
  acestream_channels: AcestreamChannel[];
}
export interface EpgSource {
  id: number;
  url: string;
  name: string;
  enabled: boolean;
  last_updated: string | null;
  error_count: number;
  last_error: string | null;
}
export interface EpgChannel {
  id: number;
  epg_source_id: number;
  channel_xml_id: string;
  name: string;
  icon_url: string | null;
  language: string | null;
}
export interface EpgProgram {
  id: number;
  epg_channel_id: number;
  start_time: string;
  end_time: string;
  title: string;
}
export interface BaseUrl {
  id: number;
  name: string;
  pattern: string;
  is_default: boolean;
}
export interface SearchResult {
  id: string;
  name: string;
  bitrate: number | null;
  categories: string[];
}
export interface SearchResponse {
  success: boolean;
  results: SearchResult[];
  pagination: { page: number; page_size: number; total_results: number; total_pages: number };
}
export interface BackgroundTask {
  task_name: string;
  last_run: string | null;
  next_run: string | null;
  status: string;
  last_error: string | null;
  last_result: unknown;
  progress: unknown;
}

async function json<T>(res: APIResponse, what: string): Promise<T> {
  if (!res.ok()) {
    throw new Error(`${what} failed: HTTP ${res.status()} ${(await res.text()).slice(0, 400)}`);
  }
  return (await res.json()) as T;
}

/**
 * Typed helper over Playwright's request context. Used for seeding, polling
 * background jobs and cross-checking what the UI shows against the API.
 */
export class Api {
  constructor(private readonly request: APIRequestContext, readonly baseURL: string) {}

  private url(path: string): string {
    return `${this.baseURL}${path}`;
  }

  /* health / config */
  health(): Promise<HealthResponse> {
    return this.request.get(this.url('/api/v1/health')).then((r) => json<HealthResponse>(r, 'GET /health'));
  }
  async getSetting(key: string): Promise<string> {
    const body = await this.request.get(this.url(`/api/v1/config/${key}`)).then((r) => json<{ key: string; value: string }>(r, `GET /config/${key}`));
    return body.value;
  }
  async putSetting(key: string, value: string): Promise<void> {
    await json(await this.request.put(this.url(`/api/v1/config/${key}`), { data: { value } }), `PUT /config/${key}`);
  }
  backgroundTasks(): Promise<BackgroundTask[]> {
    return this.request.get(this.url('/api/v1/background-tasks/status')).then((r) => json<BackgroundTask[]>(r, 'GET /background-tasks/status'));
  }

  /* scraper urls */
  listUrls(): Promise<UrlResponse[]> {
    return this.request.get(this.url('/api/v1/scrapers/urls?limit=500')).then((r) => json<UrlResponse[]>(r, 'GET /scrapers/urls'));
  }
  async findUrl(url: string): Promise<UrlResponse | undefined> {
    return (await this.listUrls()).find((u) => u.url === url);
  }
  createUrl(body: { url: string; url_type?: string; enabled?: boolean; scrape_bare_ids?: boolean }): Promise<UrlResponse> {
    return this.request.post(this.url('/api/v1/scrapers/urls'), { data: body }).then((r) => json<UrlResponse>(r, 'POST /scrapers/urls'));
  }
  async deleteUrl(id: number): Promise<void> {
    const res = await this.request.delete(this.url(`/api/v1/scrapers/urls/${id}`));
    if (!res.ok() && res.status() !== 404) throw new Error(`DELETE /scrapers/urls/${id} -> ${res.status()}`);
  }
  async triggerScrape(id: number): Promise<void> {
    await json(await this.request.post(this.url(`/api/v1/scrapers/urls/${id}/scrape`)), `POST /scrapers/urls/${id}/scrape`);
  }
  /** Wait until the URL's `last_processed` moves past `since` (scrape ran, OK or Error). */
  waitForScrape(url: string, since: string | null, timeoutMs: number): Promise<UrlResponse> {
    return pollUntil(
      async () => (await this.findUrl(url)) as UrlResponse,
      (u) => Boolean(u && u.last_processed && u.last_processed !== since),
      { timeoutMs, intervalMs: 3_000, label: `scrape of ${url}` },
    );
  }

  /* acestream channels */
  listChannels(params: Record<string, string | number | boolean> = {}): Promise<Paged<AcestreamChannel>> {
    const qs = new URLSearchParams({ page: '1', page_size: '100', ...Object.fromEntries(Object.entries(params).map(([k, v]) => [k, String(v)])) });
    return this.request.get(this.url(`/api/v1/acestream-channels/?${qs}`)).then((r) => json<Paged<AcestreamChannel>>(r, 'GET /acestream-channels'));
  }
  async getChannel(id: string): Promise<AcestreamChannel | undefined> {
    const res = await this.request.get(this.url(`/api/v1/acestream-channels/${id}`));
    if (res.status() === 404) return undefined;
    return json<AcestreamChannel>(res, `GET /acestream-channels/${id}`);
  }
  createChannel(body: { id: string; name: string; group?: string; source_url?: string }): Promise<AcestreamChannel> {
    return this.request.post(this.url('/api/v1/acestream-channels/'), { data: body }).then((r) => json<AcestreamChannel>(r, 'POST /acestream-channels'));
  }
  async deleteChannel(id: string): Promise<void> {
    const res = await this.request.delete(this.url(`/api/v1/acestream-channels/${id}`));
    if (!res.ok() && res.status() !== 404) throw new Error(`DELETE /acestream-channels/${id} -> ${res.status()}`);
  }

  /* search (engine) */
  search(query: string, perPage = 10): Promise<SearchResponse> {
    const qs = new URLSearchParams({ query, page: '1', per_page: String(perPage) });
    return this.request.get(this.url(`/api/v1/search?${qs}`)).then((r) => json<SearchResponse>(r, 'GET /search'));
  }

  /* tv channels */
  listTvChannels(search?: string): Promise<Paged<TvChannel>> {
    const qs = new URLSearchParams({ skip: '0', limit: '500' });
    if (search) qs.set('search', search);
    return this.request.get(this.url(`/api/v1/tv-channels/?${qs}`)).then((r) => json<Paged<TvChannel>>(r, 'GET /tv-channels'));
  }
  async findTvChannel(name: string): Promise<TvChannel | undefined> {
    return (await this.listTvChannels(name)).items.find((t) => t.name === name);
  }
  getTvChannel(id: number): Promise<TvChannel> {
    return this.request.get(this.url(`/api/v1/tv-channels/${id}`)).then((r) => json<TvChannel>(r, `GET /tv-channels/${id}`));
  }
  createTvChannel(body: { name: string; category?: string; epg_id?: string; epg_source_id?: number }): Promise<TvChannel> {
    return this.request.post(this.url('/api/v1/tv-channels/'), { data: body }).then((r) => json<TvChannel>(r, 'POST /tv-channels'));
  }
  async deleteTvChannel(id: number): Promise<void> {
    const res = await this.request.delete(this.url(`/api/v1/tv-channels/${id}`));
    if (!res.ok() && res.status() !== 404) throw new Error(`DELETE /tv-channels/${id} -> ${res.status()}`);
  }
  async associate(tvId: number, acestreamId: string): Promise<void> {
    await json(await this.request.post(this.url(`/api/v1/tv-channels/${tvId}/acestreams`), { data: { acestream_channel_id: acestreamId } }), 'POST /tv-channels/{id}/acestreams');
  }

  /* epg */
  listEpgSources(): Promise<EpgSource[]> {
    return this.request.get(this.url('/api/v1/epg/sources?limit=100')).then((r) => json<EpgSource[]>(r, 'GET /epg/sources'));
  }
  async findEpgSource(url: string): Promise<EpgSource | undefined> {
    return (await this.listEpgSources()).find((s) => s.url === url);
  }
  getEpgSource(id: number): Promise<EpgSource> {
    return this.request.get(this.url(`/api/v1/epg/sources/${id}`)).then((r) => json<EpgSource>(r, `GET /epg/sources/${id}`));
  }
  createEpgSource(body: { url: string; name: string; enabled?: boolean }): Promise<EpgSource> {
    return this.request.post(this.url('/api/v1/epg/sources'), { data: body }).then((r) => json<EpgSource>(r, 'POST /epg/sources'));
  }
  async deleteEpgSource(id: number): Promise<void> {
    const res = await this.request.delete(this.url(`/api/v1/epg/sources/${id}`), { timeout: 600_000 });
    if (!res.ok() && res.status() !== 404) throw new Error(`DELETE /epg/sources/${id} -> ${res.status()}`);
  }
  async refreshEpgSource(id: number): Promise<void> {
    await json(await this.request.post(this.url(`/api/v1/epg/sources/${id}/refresh`)), `POST /epg/sources/${id}/refresh`);
  }
  /** Wait for `last_updated` to move past `since`; the caller then inspects error_count/last_error. */
  waitForEpgRefresh(id: number, since: string | null, timeoutMs: number): Promise<EpgSource> {
    return pollUntil(() => this.getEpgSource(id), (s) => Boolean(s.last_updated && s.last_updated !== since), {
      timeoutMs,
      intervalMs: 5_000,
      label: `EPG refresh of source ${id}`,
    });
  }
  listEpgChannels(sourceId?: number, limit = 100, skip = 0): Promise<Paged<EpgChannel>> {
    const qs = new URLSearchParams({ limit: String(limit), skip: String(skip) });
    if (sourceId !== undefined) qs.set('source_id', String(sourceId));
    return this.request.get(this.url(`/api/v1/epg/channels?${qs}`)).then((r) => json<Paged<EpgChannel>>(r, 'GET /epg/channels'));
  }
  async resolveEpgChannel(sourceId: number, xmlId: string): Promise<EpgChannel | undefined> {
    const qs = new URLSearchParams({ source_id: String(sourceId), channel_xml_id: xmlId });
    const res = await this.request.get(this.url(`/api/v1/epg/channels/resolve?${qs}`));
    if (res.status() === 404) return undefined;
    return json<EpgChannel>(res, 'GET /epg/channels/resolve');
  }
  epgPrograms(channelId: number, limit = 100): Promise<EpgProgram[]> {
    return this.request.get(this.url(`/api/v1/epg/channels/${channelId}/programs?limit=${limit}`)).then((r) => json<EpgProgram[]>(r, 'GET /epg/channels/{id}/programs'));
  }
  async mapEpgChannel(epgChannelId: number, tvChannelId: number): Promise<void> {
    const res = await this.request.post(this.url('/api/v1/epg/channels/map'), { data: { epg_channel_id: epgChannelId, tv_channel_id: tvChannelId } });
    if (!res.ok()) throw new Error(`POST /epg/channels/map -> ${res.status()} ${await res.text()}`);
  }
  epgXml(params: Record<string, string> = {}): Promise<string> {
    const qs = new URLSearchParams(params);
    return this.request.get(this.url(`/api/v1/epg/xml?${qs}`)).then(async (r) => {
      if (!r.ok()) throw new Error(`GET /epg/xml -> ${r.status()}`);
      return r.text();
    });
  }

  /* base urls + playlists */
  listBaseUrls(): Promise<BaseUrl[]> {
    return this.request.get(this.url('/api/v1/base-urls')).then((r) => json<BaseUrl[]>(r, 'GET /base-urls'));
  }
  async deleteBaseUrl(id: number): Promise<void> {
    const res = await this.request.delete(this.url(`/api/v1/base-urls/${id}`));
    if (!res.ok() && res.status() !== 404) throw new Error(`DELETE /base-urls/${id} -> ${res.status()}`);
  }
  async playlist(path = '/api/v1/playlists/m3u', params: Record<string, string> = {}): Promise<{ status: number; body: string; contentType: string }> {
    const qs = new URLSearchParams(params);
    const res = await this.request.get(this.url(`${path}${qs.size ? `?${qs}` : ''}`));
    return { status: res.status(), body: await res.text(), contentType: res.headers()['content-type'] ?? '' };
  }
  async raw(method: 'get' | 'post' | 'put' | 'delete', path: string, data?: unknown): Promise<APIResponse> {
    return this.request[method](this.url(path), data === undefined ? undefined : { data });
  }
}
