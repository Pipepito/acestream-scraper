/**
 * Type definitions for WARP-related data
 */

/**
 * Enum for WARP modes
 */
export enum WarpMode {
  WARP = 'warp',
  DOT = 'dot',
  PROXY = 'proxy',
  OFF = 'off'
}

/**
 * Interface for WARP status response
 */
export interface WarpStatus {
  running: boolean;
  connected: boolean;
  mode: WarpMode | null;
  account_type: string;
  ip: string | null;
  cf_trace: Record<string, string>;
}

/**
 * Interface for WARP license request
 */
export interface WarpLicenseRequest {
  license_key: string;
}

/**
 * Interface for WARP mode request
 */
export interface WarpModeRequest {
  mode: WarpMode;
}

/**
 * Interface for WARP response
 */
export interface WarpResponse {
  success: boolean;
  message: string;
  details: Record<string, any> | null;
}
