import i18next from 'i18next';
import { getLocale } from '../i18n/locale';
import { uiText } from '../i18n/text';
/**
 * Human formatting shared across pages. Everything a user reads that comes
 * from the API as a raw number, id or timestamp goes through here.
 */

/** Engine bitrates arrive in bits per second. */
export const formatBitrate = (bitsPerSecond?: number | null): string => {
  if (!bitsPerSecond || bitsPerSecond <= 0) return uiText('Unknown');
  if (bitsPerSecond >= 1_000_000) return `${(bitsPerSecond / 1_000_000).toLocaleString(getLocale(), { minimumFractionDigits: 1, maximumFractionDigits: 1 })} Mbps`;
  return `${Math.round(bitsPerSecond / 1000)} kbps`;
};

const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`;

/** "12 min ago", "in 23 h", "3 days ago", "just now", "never". */
export const formatRelativeTime = (iso?: string | null, now: Date = new Date()): string => {
  if (!iso) return uiText('never');
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return uiText('never');
  const diffMs = then.getTime() - now.getTime();
  const past = diffMs < 0;
  const abs = Math.abs(diffMs);
  const minutes = Math.round(abs / 60_000);
  const hours = Math.round(abs / 3_600_000);
  const days = Math.round(abs / 86_400_000);
  if (getLocale() === 'es-ES' && abs >= 45_000) {
    const unit = minutes < 60 ? 'minute' : hours < 48 ? 'hour' : 'day';
    const amount = minutes < 60 ? minutes : hours < 48 ? hours : days;
    return new Intl.RelativeTimeFormat(getLocale(), { numeric: 'always', style: 'short' }).format(past ? -amount : amount, unit);
  }
  let phrase: string;
  if (abs < 45_000) return uiText('just now');
  if (minutes < 60) phrase = `${minutes} min`;
  else if (hours < 48) phrase = `${hours} h`;
  else phrase = plural(days, 'day', 'days');
  return past ? `${phrase} ago` : `in ${phrase}`;
};

const jobText = i18next.getFixedT(null, 'jobs');
const jobIds = ['url_scraping', 'epg_refresh', 'epg_program_cleanup', 'channel_status', 'channel_cleanup',
  'offline_stream_cleanup', 'activity_log_cleanup', 'media_server_sync', 'v1_epg_programs_migration'] as const;
export const formatJobName = (id: string): string => {
  const manual = id.startsWith('manual_');
  const key = manual ? id.slice(7) : id;
  const known = jobIds.find(value => value === key);
  const name = known ? jobText(known) : key.replace(/_/g, ' ');
  return manual ? jobText('manual', { name }) : name;
};
const num = (value: unknown): number | null => typeof value === 'number' && Number.isFinite(value) ? value : null;
const object = (value: unknown): Record<string, unknown> => value && typeof value === 'object' ? value as Record<string, unknown> : {};
const field = (value: unknown, key: string): number | null => num(object(value)[key]);

/** Whole localized metrics retain online/offline/skipped/error distinctions and scalar results. */
export const summarizeJobResult = (id: string, result: unknown): string | null => {
  if (result == null) return null;
  const values = object(result);
  switch (id.startsWith('manual_') ? id.slice(7) : id) {
    case 'url_scraping': {
      const processed = field(result, 'processed');
      if (processed === null) return null;
      const parts: string[] = [jobText('scrape', { sources: jobText('sources', { count: processed }), errors: jobText('errors', { count: field(result, 'failures') ?? 0 }) })];
      const events = values.events;
      const updated = field(events, 'updated') ?? 0, pending = field(events, 'pending') ?? 0;
      const failed = field(events, 'failures') ?? 0, deferred = field(events, 'deferred') ?? 0;
      if (updated || pending || failed || deferred) parts.push(jobText('events', { updated, pending, failed, deferred }));
      const searches = values.saved_searches;
      if (searches) parts.push(jobText('searches', {
        added: field(searches, 'added') ?? 0, existing: field(searches, 'existing') ?? 0,
        excluded: field(searches, 'excluded_candidates') ?? 0, unresolved: field(searches, 'unresolved_candidates') ?? 0,
        partial: field(searches, 'partial') ?? 0, failed: field(searches, 'failed') ?? 0,
        skipped: field(searches, 'skipped') ?? 0, interrupted: field(searches, 'interrupted') ?? 0,
        deferredCandidates: field(searches, 'deferred_candidates') ?? 0, deferredSearches: field(searches, 'deferred_searches') ?? 0,
      }));
      const excluded = field(values.import_exclusions, 'excluded_candidates') ?? 0;
      if (excluded) parts.push(jobText('excluded', { count: excluded }));
      return parts.join('; ');
    }
    case 'channel_status': {
      if (values.message_code === 'CHECK_ENGINE_NOT_CONFIGURED') return jobText('noEngine');
      if (typeof values.message === 'string') return getLocale() === 'en-US' ? values.message : jobText('legacyDetail');
      const checked = field(result, 'checked');
      if (checked === null) return null;
      const online = field(result, 'online'), offline = field(result, 'offline');
      const deferred = field(result, 'deferred') ?? 0;
      return jobText('checked', { checked, skipped: field(result, 'skipped') ?? 0,
        signal: online !== null && offline !== null ? jobText('signal', { online, offline }) : '',
        errors: jobText('errors', { count: field(result, 'failed') ?? 0 }),
        deferred: deferred > 0 ? jobText('deferred', { count: deferred, reason: jobText(values.stop_reason === 'viewing' ? 'viewing' : 'shutdown') }) : '',
      });
    }
    case 'epg_refresh': {
      const sources = field(result, 'sources');
      if (sources === null) return null;
      const successful = field(result, 'successful') ?? 0, failed = field(result, 'failed') ?? 0;
      return failed ? jobText('partialRefresh', { successful, sources: jobText('sources', { count: sources }), failed }) : jobText('refreshed', { count: successful });
    }
    case 'epg_program_cleanup': {
      if (values.disabled === true) return jobText('retentionDisabled');
      const deleted = field(result, 'deleted');
      return deleted === null ? null : jobText('programmesRemoved', { count: deleted });
    }
    case 'offline_stream_cleanup': {
      if (values.status === 'deferred') return jobText('cleanupDeferred');
      if (values.status === 'disabled') return jobText('cleanupDisabled');
      const deleted = field(result, 'deleted');
      const failures = field(result, 'rescrape_failures') ?? 0;
      return deleted === null ? null : jobText('streamCleanup', { removed: jobText('streamsRemoved', { count: deleted }),
        refreshed: jobText('refreshed', { count: field(result, 'rescraped') ?? 0 }), failures: failures ? jobText('refreshFailures', { count: failures }) : '' });
    }
    case 'channel_cleanup': {
      const deleted = field(result, 'deleted');
      if (deleted === null) return null;
      const events = field(values.events, 'deleted') ?? 0;
      return [jobText('channelsRemoved', { count: deleted }), ...(events ? [jobText('eventsRemoved', { count: events })] : [])].join('; ');
    }
    case 'activity_log_cleanup': {
      const count = num(result) ?? field(result, 'deleted');
      return count === null ? null : jobText('entriesRemoved', { count });
    }
    default: return null;
  }
};
