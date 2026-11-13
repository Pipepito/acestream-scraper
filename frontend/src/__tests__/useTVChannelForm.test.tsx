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
  epg_source_id: 4,
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

describe('guide source in the edit form', () => {
  const submit = (value: string | number | null) => {
    const { result } = renderHook(() => useTVChannelForm());
    act(() => result.current.handleOpenEditDialog(channel));
    if (value !== null) {
      act(() => result.current.handleFormChange({ target: { name: 'epg_source_id', value, type: 'text', checked: false } } as unknown as React.ChangeEvent<HTMLInputElement>));
    }
    let payload: ReturnType<typeof result.current.validateForm> = null;
    act(() => {
      payload = result.current.validateForm();
    });
    return payload;
  };

  it('keeps the loaded source', () => {
    expect(submit(null)).toHaveProperty('epg_source_id', 4);
  });

  it('sends the chosen source as a number', () => {
    expect(submit(9)).toHaveProperty('epg_source_id', 9);
  });

  it('sends null when set to Not set', () => {
    expect(submit('')).toHaveProperty('epg_source_id', null);
  });
});
