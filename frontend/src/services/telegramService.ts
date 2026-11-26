import i18next from 'i18next';
import { getLocale } from '../i18n/locale';
import type { ExtractionRecipe } from '../recipes/types';
import type { components } from '../types/api-generated';
import { getErrorMessage } from '../utils/errorUtils';
import apiClient,{ ApiError } from './apiClient';

type Schemas = components['schemas'];
export type TelegramStatus = Schemas['TelegramStatus'];
export type TelegramPeer = Schemas['TelegramPeer'];
export type TelegramSource = Schemas['TelegramSource'];
export type TelegramSourceConfig = Schemas['TelegramSourceConfig'];
export type TelegramPreview = Schemas['TelegramPreview'];
export type TelegramSourceCreate = Schemas['TelegramSourceCreate'];

const configKeys = ['name', 'chat_id', 'topic_id', 'enabled', 'sender_ids', 'sender_rule', 'include_forwards', 'include', 'exclude', 'filter_mode', 'bare_ids', 'recipe'] as const;
// Explicit projection prevents response metadata from becoming rejected write fields.
const sourceConfig = (source: TelegramSourceCreate): TelegramSourceConfig => Object.fromEntries(
  configKeys.filter(key => Object.prototype.hasOwnProperty.call(source, key)).map(key => [key, source[key]])
) as TelegramSourceConfig;

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
      : post<TelegramSource>('/sources', { ...sourceConfig(source), ...(source.history_count !== undefined ? { history_count: source.history_count } : {}), ...(source.history_since !== undefined ? { history_since: source.history_since } : {}) }),
    remove: async (id: number): Promise<void> => { await apiClient.delete(`/v1/telegram/sources/${id}`, config); },
    scan: (id: number) => post(`/sources/${id}/scan`),
  };
};
export type TelegramService = ReturnType<typeof telegramService>;

/** Resolve protocol codes on render, so an existing notice follows language changes. */
export function telegramMessage(message: string, code?: string | null): string {
  if (code && i18next.exists(code, { ns: 'errors', lng: 'en' })) return i18next.t(code, { ns: 'errors', defaultValue: i18next.t('TELEGRAM_OPERATION_FAILED', { ns: 'errors' }) });
  return getLocale() === 'en-US' ? message : i18next.t('TELEGRAM_OPERATION_FAILED', { ns: 'errors' });
}
export function telegramError(error: unknown): string {
  if (error instanceof ApiError && !error.code && getLocale() === 'en-US' && [400, 403, 409, 422, 429, 503].includes(error.status)) return error.message;
  return getErrorMessage(error);
}
