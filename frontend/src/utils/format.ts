/**
 * Human formatting shared across pages. Everything a user reads that comes
 * from the API as a raw number, id or timestamp goes through here.
 */

/** Engine bitrates arrive in bits per second. */
export const formatBitrate = (bitsPerSecond?: number | null): string => {
  if (!bitsPerSecond || bitsPerSecond <= 0) return 'Unknown';
  if (bitsPerSecond >= 1_000_000) return `${(bitsPerSecond / 1_000_000).toFixed(1)} Mbps`;
  return `${Math.round(bitsPerSecond / 1000)} kbps`;
};

const plural = (n: number, one: string, many: string): string => `${n} ${n === 1 ? one : many}`;

/** "12 min ago", "in 23 h", "3 days ago", "just now", "never". */
export const formatRelativeTime = (iso?: string | null, now: Date = new Date()): string => {
  if (!iso) return 'never';
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return 'never';
  const diffMs = then.getTime() - now.getTime();
  const past = diffMs < 0;
  const abs = Math.abs(diffMs);
  const minutes = Math.round(abs / 60_000);
  const hours = Math.round(abs / 3_600_000);
  const days = Math.round(abs / 86_400_000);
  let phrase: string;
  if (abs < 45_000) return 'just now';
  if (minutes < 60) phrase = `${minutes} min`;
  else if (hours < 48) phrase = `${hours} h`;
  else phrase = plural(days, 'day', 'days');
  return past ? `${phrase} ago` : `in ${phrase}`;
};

export const JOB_NAMES: Record<string, string> = {
  url_scraping: 'Scrape sources',
  epg_refresh: 'Refresh EPG',
  epg_program_cleanup: 'Purge old programmes',
  channel_status: 'Check stream status',
  channel_cleanup: 'Remove stale channels',
  activity_log_cleanup: 'Clean activity log',
  media_server_sync: 'Sync media servers',
  v1_epg_programs_migration: 'Migrate v1 EPG programmes',
};

export const formatJobName = (id: string): string => id.startsWith('manual_')
  ? `${JOB_NAMES[id.slice(7)] ?? id.slice(7).replace(/_/g, ' ')} (manual)`
  : JOB_NAMES[id] ?? id.replace(/_/g, ' ');

const num = (value: unknown): number | null => (typeof value === 'number' && Number.isFinite(value) ? value : null);
const field = (result: unknown, key: string): number | null =>
  result && typeof result === 'object' ? num((result as Record<string, unknown>)[key]) : null;

/** One sentence describing a job's last result, or null when there is nothing to say. */
export const summarizeJobResult = (id: string, result: unknown): string | null => {
  if (result === null || result === undefined) return null;
  switch (id.startsWith('manual_') ? id.slice(7) : id) {
    case 'url_scraping': {
      const processed = field(result, 'processed');
      const failures = field(result, 'failures') ?? 0;
      if (processed === null) return null;
      const events = result && typeof result === 'object' ? (result as Record<string, unknown>).events : null;
      const updated = field(events, 'updated') ?? 0;
      const pending = field(events, 'pending') ?? 0;
      const failed = field(events, 'failures') ?? 0;
      const deferred = field(events, 'deferred') ?? 0;
      const summary = updated || pending || failed || deferred ? `; events: ${updated} updated, ${pending} need review, ${failed} source errors, ${deferred} deferred` : '';
      const nested = result && typeof result === 'object' ? result as Record<string, unknown> : {};
      const searches = nested.saved_searches;
      const searchSummary = searches ? `; saved searches: ${field(searches, 'added') ?? 0} added, ${field(searches, 'existing') ?? 0} existing, ${field(searches, 'excluded_candidates') ?? 0} excluded, ${field(searches, 'unresolved_candidates') ?? 0} unresolved, ${field(searches, 'partial') ?? 0} partial, ${field(searches, 'failed') ?? 0} failed, ${field(searches, 'skipped') ?? 0} skipped, ${field(searches, 'interrupted') ?? 0} interrupted, ${field(searches, 'deferred_candidates') ?? 0} candidates deferred, ${field(searches, 'deferred_searches') ?? 0} searches deferred` : '';
      const excluded = field(nested.import_exclusions, 'excluded_candidates') ?? 0;
      return `${plural(processed, 'source', 'sources')}, ${plural(failures, 'error', 'errors')}${summary}${searchSummary}${excluded ? `; ${excluded} source candidates excluded` : ''}`;
    }
    case 'channel_status': {
      const checked = field(result, 'checked');
      const failed = field(result, 'failed') ?? 0;
      if (result && typeof result === 'object' && typeof (result as Record<string, unknown>).message === 'string') {
        return (result as Record<string, string>).message;
      }
      if (checked === null) return null;
      const online = field(result, 'online');
      const offline = field(result, 'offline');
      const skipped = field(result, 'skipped') ?? 0;
      const counts = online !== null && offline !== null ? `, ${online} online, ${offline} offline` : '';
      const deferred = field(result, 'deferred') ?? 0;
      const reason = result && typeof result === 'object' && (result as Record<string, unknown>).stop_reason === 'viewing'
        ? 'playback active' : 'application stopping';
      const incomplete = deferred > 0 ? `, ${deferred} deferred (${reason})` : '';
      return `${checked} checked${counts}, ${skipped} skipped, ${plural(failed, 'error', 'errors')}${incomplete}`;
    }
    case 'epg_refresh': {
      const sources = field(result, 'sources');
      const successful = field(result, 'successful') ?? 0;
      const failed = field(result, 'failed') ?? 0;
      if (sources === null) return null;
      if (failed === 0) return `${plural(successful, 'source', 'sources')} refreshed`;
      return `${successful} of ${plural(sources, 'source', 'sources')} refreshed, ${failed} failed`;
    }
    case 'epg_program_cleanup': {
      if (result && typeof result === 'object' && (result as Record<string, unknown>).disabled === true) return 'retention disabled';
      const deleted = field(result, 'deleted');
      return deleted === null ? null : `${deleted} programmes removed`;
    }
    case 'channel_cleanup': {
      const deleted = field(result, 'deleted');
      const events = result && typeof result === 'object' ? (result as Record<string, unknown>).events : null;
      const eventCount = field(events, 'deleted') ?? 0;
      return deleted === null ? null : `${deleted} channels removed${eventCount ? `; ${eventCount} events removed` : ''}`;
    }
    case 'activity_log_cleanup': {
      const n = num(result) ?? field(result, 'deleted');
      return n === null ? null : `${plural(n, 'entry', 'entries')} removed`;
    }
    default:
      return null;
  }
};
