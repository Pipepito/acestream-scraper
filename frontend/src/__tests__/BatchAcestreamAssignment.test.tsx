import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import BatchAcestreamAssignment from '../components/BatchAcestreamAssignment';

const mockMutateAsync = jest.fn();

jest.mock('../hooks/useTVChannels', () => ({
  useBatchAssignAcestreams: () => ({ mutateAsync: mockMutateAsync, isPending: false }),
}));

describe('BatchAcestreamAssignment', () => {
  beforeEach(() => {
    mockMutateAsync.mockReset();
    mockMutateAsync.mockResolvedValue({ success_count: 2, failure_count: 0, details: { '7': { success: ['a', 'b'], failure: [] } } });
  });

  it('posts the batch-assign body the backend schema expects', async () => {
    render(<BatchAcestreamAssignment open onClose={jest.fn()} tvChannelId={7} tvChannelName="Arena" />);

    fireEvent.change(screen.getByRole('textbox', { name: 'Acestream IDs' }), { target: { value: 'aaaa, bbbb\ncccc' } });
    fireEvent.click(screen.getByRole('button', { name: 'Associate' }));

    await waitFor(() => expect(mockMutateAsync).toHaveBeenCalledTimes(1));
    expect(mockMutateAsync).toHaveBeenCalledWith({
      assignments: [
        { tv_channel_id: 7, acestream_channel_id: 'aaaa' },
        { tv_channel_id: 7, acestream_channel_id: 'bbbb' },
        { tv_channel_id: 7, acestream_channel_id: 'cccc' },
      ],
    });
    expect(await screen.findByText(/Successfully associated 2 acestreams/)).toBeInTheDocument();
  });
});
