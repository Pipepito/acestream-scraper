/**
 * Service for interacting with WARP API
 */
import apiClient from './apiClient';
import { 
  WarpStatus, 
  WarpResponse, 
  WarpLicenseRequest, 
  WarpModeRequest,
  WarpMode
} from '../types/warpTypes';

// apiClient already carries the '/api' base; only the versioned path belongs here.
const API_PATH = '/v1/warp';

/**
 * Get current WARP status
 */
export const getWarpStatus = async (): Promise<WarpStatus> => {
  const response = await apiClient.get<WarpStatus>(`${API_PATH}/status`);
  return response.data;
};

/**
 * Connect to WARP
 */
export const connectWarp = async (): Promise<WarpResponse> => {
  const response = await apiClient.post<WarpResponse>(`${API_PATH}/connect`);
  return response.data;
};

/**
 * Disconnect from WARP
 */
export const disconnectWarp = async (): Promise<WarpResponse> => {
  const response = await apiClient.post<WarpResponse>(`${API_PATH}/disconnect`);
  return response.data;
};

/**
 * Set WARP mode
 */
export const setWarpMode = async (mode: WarpMode): Promise<WarpResponse> => {
  const request: WarpModeRequest = { mode };
  const response = await apiClient.post<WarpResponse>(`${API_PATH}/mode`, request);
  return response.data;
};

/**
 * Register WARP license
 */
export const registerWarpLicense = async (licenseKey: string): Promise<WarpResponse> => {
  const request: WarpLicenseRequest = { license_key: licenseKey };
  const response = await apiClient.post<WarpResponse>(`${API_PATH}/license`, request);
  return response.data;
};

export type WarpExclusions = import('../types/api-generated').components['schemas']['WarpExclusionsState'];
export type WarpExclusionsUpdate = import('../types/api-generated').components['schemas']['WarpExclusionsUpdate'];
export const getWarpExclusions = async (): Promise<WarpExclusions> =>
  (await apiClient.get<WarpExclusions>(`${API_PATH}/exclusions`)).data;
export const saveWarpExclusions = async (request: WarpExclusionsUpdate): Promise<WarpExclusions> =>
  (await apiClient.put<WarpExclusions>(`${API_PATH}/exclusions`, request)).data;
