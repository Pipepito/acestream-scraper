export interface ChannelBase {
  channel_id: string;
  name: string;
}

export interface ChannelCreate extends ChannelBase {
  source_url?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
}

export interface ChannelUpdate {
  name?: string;
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  source_url?: string;
  is_active?: boolean;
  tv_channel_id?: number;
  epg_update_protected?: boolean;
}

export interface AcestreamChannel extends ChannelBase {
  id: string; // Acestream hash ID
  group?: string;
  logo?: string;
  tvg_id?: string;
  tvg_name?: string;
  source_url?: string;
  original_url?: string;
  last_seen?: string;
  is_active: boolean;
  is_online?: boolean;
  last_checked?: string;
  check_error?: string;
  epg_update_protected?: boolean;
  tv_channel_id?: number;
  added_at?: string;
  status?: string;
}

export interface ChannelStatusCheck {
  total_channels: number;
  online_count: number;
  offline_count: number;
  status_details: Record<string, any>;
}
