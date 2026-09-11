import React, { useState } from 'react';
import { TVChannel, TVChannelCreate, TVChannelUpdate } from '../types/tvChannelTypes';

export type TVChannelFormErrors = {
  name?: string;
  submit?: string;
};

const sanitizeTextInput = (value: string | undefined): string => value?.trim() ?? '';

/**
 * Hook owning the create/edit TV channel form state for the TV Channels page.
 */
export const useTVChannelForm = () => {
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<TVChannel | null>(null);
  const [formData, setFormData] = useState<TVChannelCreate | TVChannelUpdate>({
    name: '',
    logo_url: '',
    description: '',
    category: '',
    country: '',
    language: '',
    is_active: true,
  });
  const [formErrors, setFormErrors] = useState<TVChannelFormErrors>({});

  const handleOpenCreateDialog = () => {
    setFormErrors({});
    setFormData({
      name: '',
      logo_url: '',
      description: '',
      category: '',
      country: '',
      language: '',
      is_active: true,
      is_favorite: false,
    });
    setOpenCreateDialog(true);
  };

  const handleOpenEditDialog = (channel: TVChannel) => {
    setFormErrors({});
    setSelectedChannel(channel);
    setFormData({
      name: channel.name,
      logo_url: channel.logo_url || '',
      description: channel.description || '',
      category: channel.category || '',
      country: channel.country || '',
      language: channel.language || '',
      is_active: channel.is_active,
      is_favorite: channel.is_favorite,
      epg_id: channel.epg_id || '',
      channel_number: channel.channel_number,
    });
    setOpenEditDialog(true);
  };

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setFormErrors((prev) => ({ ...prev, [name]: undefined, submit: undefined }));
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : name === 'channel_number' ? (value === '' ? '' : Number(value)) : value,
    }));
  };

  const getSanitizedPayload = (): TVChannelCreate | TVChannelUpdate => ({
    ...formData,
    name: sanitizeTextInput(formData.name),
    logo_url: sanitizeTextInput(formData.logo_url),
    description: sanitizeTextInput(formData.description),
    category: sanitizeTextInput(formData.category),
    country: sanitizeTextInput(formData.country),
    language: sanitizeTextInput(formData.language),
    epg_id: 'epg_id' in formData ? sanitizeTextInput(formData.epg_id) : undefined,
  });

  const validateForm = (): TVChannelCreate | TVChannelUpdate | null => {
    const payload = getSanitizedPayload();

    if (!payload.name) {
      setFormErrors({ name: 'Enter a channel name before saving.' });
      return null;
    }

    setFormErrors({});
    return payload;
  };

  return {
    openCreateDialog,
    setOpenCreateDialog,
    openEditDialog,
    setOpenEditDialog,
    selectedChannel,
    formData,
    formErrors,
    setFormErrors,
    handleOpenCreateDialog,
    handleOpenEditDialog,
    handleFormChange,
    validateForm,
  };
};
