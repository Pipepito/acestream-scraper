import { useQuery } from '@tanstack/react-query';
import { eventService, type EventInterests } from '../services/eventService';

export type DashboardEventView = 'all' | 'following' | 'interests';
export interface DashboardEventPreferences {
  version: 1;
  view: DashboardEventView;
  zone: string;
  interests: EventInterests;
}
export const DASHBOARD_EVENTS_KEY = 'tv-dashboard-events-v1';
export function validEventZone(zone: string): boolean {
  try { new Intl.DateTimeFormat(undefined, { timeZone: zone }).format(); return Boolean(zone); } catch { return false; }
}
export function readEventPreferences(): DashboardEventPreferences {
  const fallback: DashboardEventPreferences = { version: 1, view: 'all', zone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC', interests: { sports: [], competitions: [], teams: [] } };
  try {
    const raw = localStorage.getItem(DASHBOARD_EVENTS_KEY);
    if (!raw || raw.length > 16000) return fallback;
    const data = JSON.parse(raw);
    if (data?.version !== 1 || !['all', 'following', 'interests'].includes(data.view) || typeof data.zone !== 'string' || !validEventZone(data.zone)) return fallback;
    if (!['sports', 'competitions', 'teams'].every(key => Array.isArray(data.interests?.[key]) && data.interests[key].length <= 100 && data.interests[key].every((name: unknown) => typeof name === 'string' && name.trim().length > 0 && name.length <= 200))) return fallback;
    return { version: 1, view: data.view, zone: data.zone, interests: { sports: data.interests.sports, competitions: data.interests.competitions, teams: data.interests.teams } };
  } catch { return fallback; }
}
export function saveEventPreferences(value: DashboardEventPreferences): void {
  try { localStorage.setItem(DASHBOARD_EVENTS_KEY, JSON.stringify(value)); } catch { /* Preferences remain usable in memory when storage is unavailable. */ }
}
export function useDashboardEvents(preferences: DashboardEventPreferences) {
  const hasInterests = Object.values(preferences.interests).some(names => names?.length);
  const filters = { selection: 'dashboard' as const, limit: 6, window_days: 7, search: '', sport: '', competition: '', source: '',
    zone: preferences.zone, upcoming: true, followed: preferences.view === 'following', archived: false, offset: 0,
    interests: preferences.view === 'interests' ? JSON.stringify(preferences.interests) : undefined };
  return useQuery({ queryKey: ['events', 'dashboard', filters], queryFn: () => eventService.list(filters),
    enabled: preferences.view !== 'interests' || hasInterests, refetchInterval: 60_000, refetchOnWindowFocus: true });
}
