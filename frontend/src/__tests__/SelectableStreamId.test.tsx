import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SelectableStreamId from '../components/channels/SelectableStreamId';

it('selects the complete ID for manual copying and keeps its lookup badge beside Copy', async () => {
  const id = 'a123456789'.repeat(4);
  const copy = jest.fn();
  render(<SelectableStreamId id={id} networkStatus="found" onCopyId={copy} />);
  const input = screen.getByRole('textbox') as HTMLInputElement;
  await userEvent.setup().click(screen.getByRole('button', { name: `copy acestream id ${id}` }));
  expect(input).toHaveFocus();
  expect(input.selectionStart).toBe(0);
  expect(input.selectionEnd).toBe(40);
  expect(input).toHaveAttribute('readonly');
  expect(copy).toHaveBeenCalledWith(id);
  expect(screen.getByText('ID found')).toBeInTheDocument();
});
