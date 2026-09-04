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

export const formatJobName = (id: string): string => JOB_NAMES[id] ?? id.replace(/_/g, ' ');

const num = (value: unknown): number | null => (typeof value === 'number' && Number.isFinite(value) ? value : null);
const field = (result: unknown, key: string): number | null =>
  result && typeof result === 'object' ? num((result as Record<string, unknown>)[key]) : null;

/** One sentence describing a job's last result, or null when there is nothing to say. */
export const summarizeJobResult = (id: string, result: unknown): string | null => {
  if (result === null || result === undefined) return null;
  switch (id) {
    case 'url_scraping': {
      const processed = field(result, 'processed');
      const failures = field(result, 'failures') ?? 0;
      return processed === null ? null : `${plural(processed, 'source', 'sources')}, ${plural(failures, 'error', 'errors')}`;
    }
    case 'channel_status': {
      const checked = field(result, 'checked');
      const failed = field(result, 'failed') ?? 0;
      return checked === null ? null : `${checked} checked, ${failed} offline`;
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
      return deleted === null ? null : `${deleted} channels removed`;
    }
    case 'activity_log_cleanup': {
      const n = num(result) ?? field(result, 'deleted');
      return n === null ? null : `${plural(n, 'entry', 'entries')} removed`;
    }
    default:
      return null;
  }
};
