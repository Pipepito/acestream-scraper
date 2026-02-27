import { AcestreamChannel } from './channelTypes';

export interface TVChannelBase {
  name: string;
  logo_url?: string;
  description?: string;
  category?: string;
  country?: string;
  language?: string;
  website?: string;
  epg_id?: string;
  channel_number?: number;
}

export interface TVChannelCreate extends TVChannelBase {
  is_active?: boolean;
  is_favorite?: boolean;
  epg_source_id?: number;
}

export interface TVChannelUpdate {
  name?: string;
  logo_url?: string;
  description?: string;
  category?: string;
  country?: string;
  language?: string;
  website?: string;
  epg_id?: string;
  is_active?: boolean;
  is_favorite?: boolean;
  channel_number?: number;
  epg_source_id?: number;
}

export interface TVChannel extends TVChannelBase {
  id: number;
  epg_source_id?: number;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  is_active: boolean;
  is_favorite: boolean;
  acestream_channels: AcestreamChannel[];
}

// For batch operations
export interface BatchAssignmentRequest {
  [tv_channel_id: string]: string[]; // Map of TV channel IDs to acestream IDs
}

export interface BatchAssignmentResult {
  success_count: number;
  failure_count: number;
  details: {
    [tv_channel_id: string]: {
      success: string[];
      failure: string[];
    };
  };
}
