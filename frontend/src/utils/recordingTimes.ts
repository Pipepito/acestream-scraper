/** Explicit IANA-zone wall time resolution, including DST gaps and folds. */
export function localRecordingTime(date: Date, zone: string): string {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: zone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date);
  const get = (key: string) => parts.find((part) => part.type === key)?.value;
  return `${get('year')}-${get('month')}-${get('day')}T${get('hour')}:${get('minute')}`;
}
export function recordingTimeChoices(local: string, zone: string): string[] {
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local)) return [];
  const nominal = Date.parse(`${local}:00Z`);
  if (!Number.isFinite(nominal)) return [];
  try {
    const values = [];
    for (let minutes = -840; minutes <= 840; minutes += 15) {
      const date = new Date(nominal + minutes * 60_000);
      if (localRecordingTime(date, zone) === local) values.push(date.toISOString());
    }
    return values;
  } catch { return []; }
}
