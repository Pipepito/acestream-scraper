import { formatBitrate, formatJobName, formatRelativeTime, summarizeJobResult } from '../utils/format';

describe('formatBitrate', () => {
  it('prints Mbps with one decimal above 1 Mbps and kbps below', () => {
    expect(formatBitrate(802401)).toBe('802 kbps');
    expect(formatBitrate(1657357)).toBe('1.7 Mbps');
    expect(formatBitrate(71253)).toBe('71 kbps');
    expect(formatBitrate(0)).toBe('Unknown');
    expect(formatBitrate(null)).toBe('Unknown');
  });
});

describe('formatRelativeTime', () => {
  const now = new Date('2026-09-02T10:12:00Z');
  it('describes past and future moments in plain units', () => {
    expect(formatRelativeTime('2026-09-02T10:00:00Z', now)).toBe('12 min ago');
    expect(formatRelativeTime('2026-09-02T10:11:40Z', now)).toBe('just now');
    expect(formatRelativeTime('2026-09-02T07:12:00Z', now)).toBe('3 h ago');
    expect(formatRelativeTime('2026-08-30T10:12:00Z', now)).toBe('3 days ago');
    expect(formatRelativeTime('2026-09-02T10:15:00Z', now)).toBe('in 3 min');
    expect(formatRelativeTime('2026-09-03T09:12:00Z', now)).toBe('in 23 h');
  });
  it('handles missing values', () => {
    expect(formatRelativeTime(null, now)).toBe('never');
    expect(formatRelativeTime('not a date', now)).toBe('never');
  });
});

describe('job names and results', () => {
  it('maps scheduler ids to plain names', () => {
    expect(formatJobName('url_scraping')).toBe('Scrape sources');
    expect(formatJobName('epg_refresh')).toBe('Refresh EPG');
    expect(formatJobName('channel_status')).toBe('Check stream status');
    expect(formatJobName('some_new_job')).toBe('some new job');
  });
  it('summarises last results per job', () => {
    expect(summarizeJobResult('url_scraping', { processed: 2, failures: 0 })).toBe('2 sources, 0 errors');
    expect(summarizeJobResult('channel_status', { checked: 6, failed: 5 })).toBe('6 checked, 5 offline');
    expect(summarizeJobResult('epg_refresh', { sources: 1, successful: 1, failed: 0 })).toBe('1 source refreshed');
    expect(summarizeJobResult('epg_refresh', { sources: 2, successful: 1, failed: 1 })).toBe('1 of 2 sources refreshed, 1 failed');
    expect(summarizeJobResult('epg_program_cleanup', { deleted: 312, disabled: false })).toBe('312 programmes removed');
    expect(summarizeJobResult('activity_log_cleanup', 4)).toBe('4 entries removed');
    expect(summarizeJobResult('channel_cleanup', { deleted: 0 })).toBe('0 channels removed');
    expect(summarizeJobResult('channel_cleanup', null)).toBeNull();
  });
});
