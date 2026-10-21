import { act, renderHook } from '@testing-library/react';
import React from 'react';
import { useTVChannelForm } from '../hooks/useTVChannelForm';
import { TVChannel } from '../types/tvChannelTypes';

const channel = {
  id: 3,
  name: 'Example Channel',
  is_active: true,
  is_favorite: false,
  epg_id: 'Example.xx',
  channel_number: 7,
  created_at: '2026-10-14T00:00:00Z',
  updated_at: '2026-10-14T00:00:00Z',
} as unknown as TVChannel;

describe('channel number in the edit form', () => {
  const submit = (value: string) => {
    const { result } = renderHook(() => useTVChannelForm());
    act(() => result.current.handleOpenEditDialog(channel));
    act(() => result.current.handleFormChange({ target: { name: 'channel_number', value, type: 'number', checked: false } } as unknown as React.ChangeEvent<HTMLInputElement>));
    let payload: ReturnType<typeof result.current.validateForm> = null;
    act(() => {
      payload = result.current.validateForm();
    });
    return payload;
  };

  it('sends null when the number is emptied, so it is removed', () => {
    expect(submit('')).toHaveProperty('channel_number', null);
  });

  it('keeps 0 as a number', () => {
    expect(submit('0')).toHaveProperty('channel_number', 0);
  });
});
