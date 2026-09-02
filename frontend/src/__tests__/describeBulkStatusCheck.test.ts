import { describeBulkStatusCheck } from '../pages/AcestreamChannels';

describe('describeBulkStatusCheck', () => {
  it('prefers the backend message', () => {
    expect(describeBulkStatusCheck({ message: 'Checked 5 channels: 1 online, 4 offline.' })).toBe('Checked 5 channels: 1 online, 4 offline.');
  });

  it('composes a count summary when the backend omits the message', () => {
    expect(describeBulkStatusCheck({ total_checked: 5, online_count: 1, offline_count: 4 })).toBe('Checked 5 channels: 1 online, 4 offline.');
  });

  it('explains background runs instead of claiming a result', () => {
    expect(describeBulkStatusCheck({ background: true, total_channels: 42, total_checked: 0 })).toMatch(/started in the background for 42 channels/);
  });
});
