import apiClient from './apiClient';
import type { components } from '../types/api-generated';

export type StartupStatus = components['schemas']['StartupStatus'];
export type RecoveryAction = components['schemas']['StartupRecoveryRequest']['action'];

export const startupService = {
  async status(): Promise<StartupStatus> {
    const data = (await apiClient.get<StartupStatus>('/v1/startup', { timeout: 10000 })).data;
    if (!data || !['starting', 'ready', 'failed'].includes(data.status) || !Array.isArray(data.events)) {
      throw new Error('Invalid startup response');
    }
    return data;
  },
  async recover(action: RecoveryAction, recoveryToken: string): Promise<StartupStatus> {
    return (await apiClient.post<StartupStatus>('/v1/startup/recover', {
      action, recovery_token: recoveryToken, confirm: action !== 'retry',
    }, { timeout: 10000 })).data;
  },
  async download(): Promise<void> {
    const response = await apiClient.get<Blob>('/v1/startup/diagnostics', { responseType: 'blob', timeout: 10000 });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'startup-diagnostics.json';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
