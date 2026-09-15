import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StreamStatistics from '../components/channels/StreamStatistics';
import type { AcestreamChannel } from '../services/channelService';

const channel: AcestreamChannel = {
  id: 'a', name: 'Sports', last_seen: '2026-09-15T10:00:00Z', status: 'active',
  is_online: null, epg_update_protected: false,
};

it('explains how to collect missing observations', async () => {
  render(<StreamStatistics channel={channel} />);
  expect(screen.getByText('Not sampled')).toBeInTheDocument();
  expect(screen.getByText('Media unknown')).toBeInTheDocument();
  await userEvent.tab();
  expect(await screen.findByRole('tooltip')).toHaveTextContent('Run Check status');
});

it('keeps zero distinct from unknown and shows the age of retained measurements', async () => {
  render(<StreamStatistics channel={{ ...channel, bitrate_bps: 8_000_000,
    bitrate_checked_at: '2026-09-14T08:00:00Z',
    stream_stats: { observed_at: '2026-09-15T08:00:00Z', peers: 0, download_speed_kbytes_sec: 0, upload_speed_kbytes_sec: null },
  }} />);
  expect(screen.getByText('0 peers · Down 0 KB/s')).toBeInTheDocument();
  expect(screen.getByText('Media 8 Mbps · Up Unknown')).toBeInTheDocument();
  expect(screen.getByText(/^Sample /)).toBeInTheDocument();
  await userEvent.tab();
  expect(await screen.findByRole('tooltip')).toHaveTextContent('not sustained throughput');
});
