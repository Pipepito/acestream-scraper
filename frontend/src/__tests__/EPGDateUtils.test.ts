import { getLocalISODate, getRelativeLocalISODate } from '../utils/dateUtils';

describe('EPG local date helpers', () => {
  it('formats dates from local calendar parts instead of UTC strings', () => {
    const date = new Date(2026, 2, 26, 23, 45, 0);

    expect(getLocalISODate(date)).toBe('2026-03-26');
  });

  it('applies day offsets using local dates', () => {
    const baseDate = new Date(2026, 2, 26, 10, 0, 0);

    expect(getRelativeLocalISODate(7, baseDate)).toBe('2026-04-02');
    expect(getRelativeLocalISODate(-1, baseDate)).toBe('2026-03-25');
  });
});
