import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CheckEngineFields from '../components/CheckEngineFields';
import * as hooks from '../hooks/useConfig';

jest.mock('../hooks/useConfig');
const mutate = jest.fn();
beforeEach(() => {
  jest.clearAllMocks();
  (hooks.useCheckEngine as jest.Mock).mockReturnValue({ data: { use_dedicated: false, url: '', managed: false } });
  (hooks.useUpdateCheckEngine as jest.Mock).mockReturnValue({ mutate, reset: jest.fn() });
});
it('explains fallback and requires an endpoint when dedicated checks are enabled', async () => {
  const user = userEvent.setup();
  render(<CheckEngineFields />);
  expect(screen.getByText(/With no engine configured, status checks are skipped/)).toBeInTheDocument();
  await user.click(screen.getByRole('checkbox', { name: 'Use a dedicated checking engine' }));
  expect(screen.getByRole('button', { name: 'Save checking engine' })).toBeDisabled();
  await user.type(screen.getByRole('textbox', { name: 'Checking engine URL' }), 'http://checker.test:6880');
  await user.click(screen.getByRole('button', { name: 'Save checking engine' }));
  await waitFor(() => expect(mutate).toHaveBeenCalledWith({ use_dedicated: true, url: 'http://checker.test:6880', managed: false }, expect.anything()));
});
it('keeps bundled checker controls in the container', () => {
  (hooks.useCheckEngine as jest.Mock).mockReturnValue({ data: { use_dedicated: true, url: 'http://localhost:6880', managed: true } });
  render(<CheckEngineFields />);
  expect(screen.getByRole('checkbox')).toBeDisabled();
  expect(screen.getByRole('textbox')).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Save checking engine' })).not.toBeInTheDocument();
});
