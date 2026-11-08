import { uiText } from '../i18n/text';
import { useUiText } from '../i18n/useUiText';
import React, { useEffect, useState } from 'react';
import { Alert, Button, Stack, TextField } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import ContentSection from './layout/ContentSection';
import { configService } from '../services/configService';
import { getErrorMessage } from '../utils/errorUtils';

export const NOTIFICATION_WEBHOOK_QUERY_KEY = ['notificationWebhookUrl'];

export interface NotificationsSectionProps {
  notify: (message: string, severity: 'success' | 'error') => void;
}

/** One webhook that hears when a scrape or a channel check ends or fails (#41). */
const NotificationsSection: React.FC<NotificationsSectionProps> = ({ notify }) => {
  const tUi = useUiText();
  const queryClient = useQueryClient();
  const { data: saved = '', isError } = useQuery({
    queryKey: NOTIFICATION_WEBHOOK_QUERY_KEY,
    queryFn: configService.getNotificationWebhookUrl,
  });
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const invalidSavedUrl = saved === '•••';

  useEffect(() => setValue(saved), [saved]);

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await configService.updateNotificationWebhookUrl(value.trim());
      notify(value.trim() ? uiText("Notification webhook saved.") : uiText("Notifications turned off."), 'success');
      await queryClient.invalidateQueries({ queryKey: NOTIFICATION_WEBHOOK_QUERY_KEY });
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    } finally {
      setBusy(false);
    }
  };

  const test = async () => {
    setBusy(true);
    try {
      await configService.testNotificationWebhook();
      notify(tUi("Test notification sent."), 'success');
    } catch (err) {
      notify(getErrorMessage(err), 'error');
    } finally {
      setBusy(false);
    }
  };

  return (
    <ContentSection
      title={tUi("Notifications")}
      description={tUi("A JSON POST after scheduled runs, manual scrapes, and individual channel checks. Skipped checks send nothing. A Gotify /message?token= URL works as it is.")}
    >
      <Stack spacing={2}>
        {isError ? <Alert severity="error">{tUi("Could not load the notification webhook. Reload to try again.")}</Alert> : null}
        {invalidSavedUrl ? (
          <Alert severity="warning">{tUi("The saved webhook URL is invalid. Replace it or clear the field to turn notifications off.")}</Alert>
        ) : null}
        <Stack
          component="form"
          direction={{ xs: 'column', sm: 'row' }}
          spacing={1}
          alignItems={{ sm: 'flex-start' }}
          onSubmit={(event: React.FormEvent) => void save(event)}
          aria-label={tUi("Notification webhook form")}
        >
          <TextField
            size="small"
            fullWidth
            label={tUi("Webhook URL")}
            placeholder={tUi("https://gotify.example/message?token=…")}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            inputProps={{ 'aria-label': uiText("Webhook URL") }}
            helperText={tUi("Leave empty to turn notifications off.")}
          />
          <Button type="submit" variant="contained" disabled={busy || value.trim() === saved}>
            {tUi("Save")}</Button>
          <Button variant="outlined" disabled={busy || !saved || invalidSavedUrl || value.trim() !== saved} onClick={() => void test()}>
            {tUi("Send test")}</Button>
        </Stack>
      </Stack>
    </ContentSection>
  );
};

export default NotificationsSection;
