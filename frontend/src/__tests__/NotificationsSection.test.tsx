import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { createAppTheme } from '../theme';
import NotificationsSection from '../components/NotificationsSection';
import { configService } from '../services/configService';

jest.mock('../services/configService', () => ({
  configService: {
    getNotificationWebhookUrl: jest.fn(),
    updateNotificationWebhookUrl: jest.fn(),
    testNotificationWebhook: jest.fn(),
  },
}));
const service = configService as jest.Mocked<typeof configService>;

const renderSection = (notify: jest.Mock) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <ThemeProvider theme={createAppTheme('light')}>
      <QueryClientProvider client={client}>
        <NotificationsSection notify={notify} />
      </QueryClientProvider>
    </ThemeProvider>,
  );
};

beforeEach(() => {
  jest.clearAllMocks();
  service.updateNotificationWebhookUrl.mockResolvedValue(undefined);
  service.testNotificationWebhook.mockResolvedValue(undefined);
});

it('saves a webhook and only offers the test once it is saved', async () => {
  service.getNotificationWebhookUrl.mockResolvedValue('');
  const user = userEvent.setup();
  const notify = jest.fn();
  renderSection(notify);
  expect(await screen.findByRole('button', { name: 'Send test' })).toBeDisabled();
  await user.type(screen.getByRole('textbox', { name: 'Webhook URL' }), ' https://gotify.test/message?token=t ');
  await user.click(screen.getByRole('button', { name: 'Save' }));
  await waitFor(() => expect(service.updateNotificationWebhookUrl).toHaveBeenCalledWith('https://gotify.test/message?token=t'));
  expect(notify).toHaveBeenCalledWith('Notification webhook saved.', 'success');
});

it('sends a test to the saved webhook', async () => {
  service.getNotificationWebhookUrl.mockResolvedValue('https://gotify.test/message?token=t');
  const user = userEvent.setup();
  const notify = jest.fn();
  renderSection(notify);
  const test = await screen.findByRole('button', { name: 'Send test' });
  await waitFor(() => expect(test).toBeEnabled());
  await user.click(test);
  await waitFor(() => expect(service.testNotificationWebhook).toHaveBeenCalled());
  expect(notify).toHaveBeenCalledWith('Test notification sent.', 'success');
});

it('turns notifications off with an empty value', async () => {
  service.getNotificationWebhookUrl.mockResolvedValue('https://gotify.test/message?token=t');
  const user = userEvent.setup();
  const notify = jest.fn();
  renderSection(notify);
  const field = await screen.findByRole('textbox', { name: 'Webhook URL' });
  await waitFor(() => expect(field).toHaveValue('https://gotify.test/message?token=t'));
  await user.clear(field);
  await user.click(screen.getByRole('button', { name: 'Save' }));
  await waitFor(() => expect(service.updateNotificationWebhookUrl).toHaveBeenCalledWith(''));
  expect(notify).toHaveBeenCalledWith('Notifications turned off.', 'success');
});

it.each(['', 'https://gotify.test/message?token=new'])(
  'lets the user recover an invalid saved webhook with %s',
  async (replacement) => {
    service.getNotificationWebhookUrl.mockResolvedValue('•••');
    const user = userEvent.setup();
    const notify = jest.fn();
    renderSection(notify);

    expect(await screen.findByRole('alert')).toHaveTextContent('The saved webhook URL is invalid');
    expect(screen.getByRole('button', { name: 'Send test' })).toBeDisabled();
    const field = screen.getByRole('textbox', { name: 'Webhook URL' });
    await waitFor(() => expect(field).toHaveValue('•••'));
    await user.clear(field);
    if (replacement) await user.type(field, replacement);
    await user.click(screen.getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(service.updateNotificationWebhookUrl).toHaveBeenCalledWith(replacement));
    expect(service.testNotificationWebhook).not.toHaveBeenCalled();
  },
);
