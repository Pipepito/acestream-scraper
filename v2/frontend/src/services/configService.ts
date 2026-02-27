import apiClient from './apiClient';

export interface Setting {
  value: string;
}

export interface StatusResponse {
  status: string;
  message: string;
  details?: string;
}

export interface HealthResponse {
  status: string;
  acestream: StatusResponse;
  settings: Record<string, string>;
  version: string;
}

export interface Stats {
  channels: {
    total: number;
    online: number;
    offline: number;
    unknown: number;
  };
  urls: {
    total: number;
    active: number;
    error: number;
  };
  epg: {
    sources: number;
    channels: number;
    programs: number;
  };
}

const BASE_URL = '/v1/config';

export const configService = {
  /**
   * Get the base URL for Acestream links
   */
  getBaseUrl: async (): Promise<string> => {
    const response = await apiClient.get<Setting>(`${BASE_URL}/base_url`);
    return response.data.value;
  },

  /**
   * Update the base URL for Acestream links
   */
  updateBaseUrl: async (baseUrl: string): Promise<void> => {
    await apiClient.put(`${BASE_URL}/base_url`, { base_url: baseUrl });
  },

  /**
   * Get the Acestream Engine URL
   */
  getAceEngineUrl: async (): Promise<string> => {
    const response = await apiClient.get<Setting>(`${BASE_URL}/ace_engine_url`);
    return response.data.value;
  },

  /**
   * Update the Acestream Engine URL
   */
  updateAceEngineUrl: async (aceEngineUrl: string): Promise<void> => {
    await apiClient.put(`${BASE_URL}/ace_engine_url`, { value: aceEngineUrl });
  },

  /**
   * Get the rescrape interval in hours
   */
  getRescrapeInterval: async (): Promise<number> => {
    const response = await apiClient.get<Setting>(`${BASE_URL}/rescrape_interval`);
    return parseInt(response.data.value);
  },

  /**
   * Update the rescrape interval
   */
  updateRescrapeInterval: async (hours: number): Promise<void> => {
    await apiClient.put(`${BASE_URL}/rescrape_interval`, { value: String(hours) });
  },

  /**
   * Get whether to add PID to Acestream links
   */
  getAddPid: async (): Promise<boolean> => {
    const response = await apiClient.get<Setting>(`${BASE_URL}/addpid`);
    return response.data.value.toLowerCase() === 'true';
  },

  /**
   * Update whether to add PID to Acestream links
   */

  updateAddPid: async (enabled: boolean): Promise<void> => {
    await apiClient.put(`${BASE_URL}/addpid`, { value: enabled ? 'true' : 'false' });
  },

  /**
   * Get whether to use AppID in Acestream links
   */
  getAppId: async (): Promise<boolean> => {
    const response = await apiClient.get<Setting>(`${BASE_URL}/appid`);
    return response.data.value.toLowerCase() === 'true';
  },

  /**
   * Update whether to use AppID in Acestream links
   */
  updateAppId: async (enabled: boolean): Promise<void> => {
    await apiClient.put(`${BASE_URL}/appid`, { value: enabled ? 'true' : 'false' });
  },

  /**
   * Get all settings
   */
  getAllSettings: async (): Promise<Record<string, string>> => {
    const response = await apiClient.get<{ settings: Record<string, string> }>(`${BASE_URL}/all`);
    return response.data.settings;
  },

  /**
   * Check the status of the Acestream Engine
   */
  checkAcestreamStatus: async (): Promise<StatusResponse> => {
    const response = await apiClient.get<StatusResponse>(`${BASE_URL}/acestream_status`);
    return response.data;
  },

  /**
   * Check the overall system health
   */
  checkHealth: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/v1/health');
    return response.data;
  },

  /**
   * Get system statistics
   */
  getStats: async (): Promise<Stats> => {
    const response = await apiClient.get<Stats>('/v1/stats');
    return response.data;
  }
};
