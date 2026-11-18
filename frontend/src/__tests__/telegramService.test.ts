import apiClient from '../services/apiClient';
import { telegramService } from '../services/telegramService';

afterEach(() => jest.restoreAllMocks());

test('history selection stays creation-only and does not invalidate recent-message preview', async () => {
  const post = jest.spyOn(apiClient, 'post').mockResolvedValue({ data: {} });
  const api = telegramService('private-admin');
  const source = { name: 'Sports', chat_id: '-100123', history_count: 100, history_since: '2026-10-01T00:00:00Z' };
  await api.preview(source);
  expect(post).toHaveBeenLastCalledWith('/v1/telegram/preview', {
    source: { name: 'Sports', chat_id: '-100123' }, limit: 10,
  }, { headers: { 'X-Telegram-Admin': 'private-admin' } });
  await api.save(source);
  expect(post).toHaveBeenLastCalledWith('/v1/telegram/sources', source, expect.anything());
});

test('source updates project writable fields while preserving false, empty and null values', async () => {
  const put = jest.spyOn(apiClient, 'put').mockResolvedValue({ data: {} });
  const source = { name: 'Original name', chat_id: '-100123', topic_id: null, enabled: false,
    sender_ids: [], include: '', bare_ids: false, recipe: null, message: 'Chat access lost',
    message_code: 'TELEGRAM_CHAT_LOST', id: 1, imported_count: 8, state: 'error' };
  await telegramService('private-admin').save(source, 1);
  expect(put).toHaveBeenCalledWith('/v1/telegram/sources/1', {
    name: 'Original name', chat_id: '-100123', topic_id: null, enabled: false,
    sender_ids: [], include: '', bare_ids: false, recipe: null,
  }, { headers: { 'X-Telegram-Admin': 'private-admin' } });
});
