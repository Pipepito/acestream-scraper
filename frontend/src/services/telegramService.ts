import apiClient, { ApiError } from './apiClient';
import { getErrorMessage } from '../utils/errorUtils';
import type { components } from '../types/api-generated';
import type { ExtractionRecipe } from '../recipes/types';

type Schemas = components['schemas'];
export type TelegramStatus = Schemas['TelegramStatus'];
export type TelegramPeer = Schemas['TelegramPeer'];
export type TelegramSource = Schemas['TelegramSource'];
export type TelegramSourceConfig = Schemas['TelegramSourceConfig'];
export type TelegramPreview = Schemas['TelegramPreview'];
export type TelegramSourceCreate = Schemas['TelegramSourceCreate'];

const sourceConfig = ({ history_count: _count, history_since: _since, ...source }: TelegramSourceCreate): TelegramSourceConfig => source;

// The caller owns this short-lived credential. Never persist it or put it in a
// React Query key, URL, browser storage, or a mutation cache.
export const telegramService = (admin: string) => {
  const config = { headers: { 'X-Telegram-Admin': admin } };
  const post = async <T>(path: string, body?: unknown): Promise<T> => (await apiClient.post(`/v1/telegram${path}`, body, config)).data;
  return {
    status: async (): Promise<TelegramStatus> => (await apiClient.get('/v1/telegram/status', config)).data,
    sources: async (): Promise<TelegramSource[]> => (await apiClient.get('/v1/telegram/sources', config)).data,
    chats: async (): Promise<TelegramPeer[]> => (await apiClient.get('/v1/telegram/chats', config)).data,
    topics: async (id: string): Promise<TelegramPeer[]> => (await apiClient.get(`/v1/telegram/chats/${encodeURIComponent(id)}/topics`, config)).data,
    preset: async (): Promise<ExtractionRecipe> => (await apiClient.get('/v1/telegram/preset', config)).data,
    login: (api_id: number, api_hash: string, phone: string) => post<TelegramStatus>('/login', { api_id, api_hash, phone }),
    code: (code: string) => post<TelegramStatus>('/code', { code }),
    password: (password: string) => post<TelegramStatus>('/password', { password }),
    disconnect: () => post<TelegramStatus>('/disconnect'),
    reconnect: () => post<TelegramStatus>('/reconnect'),
    logout: async (): Promise<TelegramStatus> => (await apiClient.delete('/v1/telegram/account', config)).data,
    resolve: (username: string) => post<TelegramPeer>('/resolve', { username }),
    preview: (source: TelegramSourceCreate) => post<TelegramPreview>('/preview', { source: sourceConfig(source), limit: 10 }),
    save: async (source: TelegramSourceCreate, id?: number): Promise<TelegramSource> => id
      ? (await apiClient.put(`/v1/telegram/sources/${id}`, sourceConfig(source), config)).data
      : post<TelegramSource>('/sources', source),
    remove: async (id: number): Promise<void> => { await apiClient.delete(`/v1/telegram/sources/${id}`, config); },
    scan: (id: number) => post(`/sources/${id}/scan`),
  };
};
export type TelegramService = ReturnType<typeof telegramService>;

/** Telegram endpoints only return fixed, sanitized operational copy. */
export function telegramError(error: unknown): string {
  if (error instanceof ApiError && [400, 403, 409, 422, 429, 503].includes(error.status)) return error.message;
  return getErrorMessage(error);
}
