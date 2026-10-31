import apiClient from './apiClient';
import type { components } from '../types/api-generated';
import { accessSession } from './accessSession';
import { clearApiToken } from './apiToken';

export type Permission = NonNullable<components['schemas']['AccountView']['permissions']>[number];
export type Account = components['schemas']['AccountView'];
export type AccessStatus = components['schemas']['AccessStatus'];
export type AccessPolicy = components['schemas']['AccessPolicy'];
export const permissionLabels: Record<Permission, string> = { live: 'Live TV', channels: 'Channels', guide: 'Programme guide', events: 'Events', recordings: 'Recordings', playlists: 'Playlists', cast: 'Cast to my devices', cast_server: 'Cast to server devices' };
const root = '/v1/auth';
export const accessService = {
  status: async (): Promise<AccessStatus> => {
    const { data } = await apiClient.get<AccessStatus>(`${root}/status`);
    accessSession.update(data.csrf, data.mode === 'accounts');
    if (data.mode === 'accounts') clearApiToken();
    return data;
  },
  bootstrap: async (data: components['schemas']['Bootstrap']) => (await apiClient.post(`${root}/bootstrap`, data)).data,
  login: async (username: string, password: string) => apiClient.post(`${root}/login`, { username, password }),
  logout: async () => apiClient.post(`${root}/logout`),
  password: async (data: components['schemas']['PasswordChange']) => apiClient.put(`${root}/password`, data),
  users: async (): Promise<Account[]> => (await apiClient.get(`${root}/users`)).data,
  createUser: async (data: components['schemas']['AccountCreate']) => apiClient.post(`${root}/users`, data),
  updateUser: async (user: Account) => apiClient.put(`${root}/users/${user.id}`, { enabled: user.enabled, administrator: user.administrator, permissions: user.permissions }),
  policy: async (): Promise<AccessPolicy> => (await apiClient.get(`${root}/policy`)).data,
  savePolicy: async (data: AccessPolicy): Promise<AccessPolicy> => (await apiClient.put(`${root}/policy`, data)).data,
  disable: async (current_password: string) => apiClient.post(`${root}/disable`, { current_password }),
  sessions: async (): Promise<components['schemas']['SessionView'][]> => (await apiClient.get(`${root}/sessions`)).data,
  revokeSession: async (id: string) => apiClient.delete(`${root}/sessions/${id}`),
  credentials: async (): Promise<components['schemas']['CredentialView'][]> => (await apiClient.get(`${root}/credentials`)).data,
  issueCredential: async (label: string, kind: 'admin' | 'playback'): Promise<components['schemas']['CredentialIssued']> => (await apiClient.post(`${root}/credentials`, { label, kind })).data,
  revokeCredential: async (id: string) => apiClient.delete(`${root}/credentials/${id}`),
  playlistLink: async (): Promise<components['schemas']['PlaylistLink']> => (await apiClient.post('/v1/view/playlists')).data,
};
