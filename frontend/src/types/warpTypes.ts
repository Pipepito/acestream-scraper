/**
 * Type definitions for WARP-related data
 */

/**
 * Enum for WARP modes
 */
export enum WarpMode {
  WARP = 'warp',
  DOH = 'doh',
  WARP_DOH = 'warp+doh',
  WARP_DOT = 'warp+dot',
  TUNNEL_ONLY = 'tunnel_only',
  DOT = 'dot',
  PROXY = 'proxy',
  OFF = 'off'
}

/**
 * Interface for WARP status response
 */
export interface WarpTunnelDetails {
  protocol?: string | null;
  endpoints?: string | null;
  last_handshake?: string | null;
  sent?: string | null;
  received?: string | null;
  latency?: string | null;
  loss?: string | null;
  colo?: string | null;
  tls_version?: string | null;
}

export interface WarpRegistrationDetails {
  account_id?: string | null;
  device_id?: string | null;
  /** Masked by the backend (first and last characters only). */
  license?: string | null;
}

/** The guard that blocks direct traffic while WARP is not in charge. */
export interface WarpKillSwitch {
  enabled: boolean;
  /** Read from the firewall; null when the server cannot tell. */
  blocking: boolean | null;
  /** WARP is not in charge and nothing blocks direct traffic. */
  unprotected?: boolean;
  /** Wanted, but this host could not install it. */
  unavailable?: boolean;
}

export interface WarpStatus {
  running: boolean;
  connected: boolean;
  mode: WarpMode | null;
  account_type: string;
  ip: string | null;
  location?: string | null;
  colo?: string | null;
  tunnel?: WarpTunnelDetails;
  registration?: WarpRegistrationDetails;
  cf_trace: Record<string, string>;
  kill_switch?: WarpKillSwitch;
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
