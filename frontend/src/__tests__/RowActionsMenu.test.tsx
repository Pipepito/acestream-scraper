import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import RowActionsMenu from '../components/RowActionsMenu';

describe('RowActionsMenu', () => {
  it('opens a labelled menu and runs the chosen action', () => {
    const edit = jest.fn();
    const remove = jest.fn();
    render(<RowActionsMenu label="More actions for DAZN1" actions={[{ label: 'Edit', onClick: edit }, { label: 'Delete', onClick: remove, danger: true }, { label: 'Harvest bare IDs', onClick: jest.fn(), checked: true }]} />);
    fireEvent.click(screen.getByRole('button', { name: 'More actions for DAZN1' }));
    const menu = screen.getByRole('menu');
    expect(menu).toBeInTheDocument();
    expect(screen.getByRole('menuitemcheckbox', { name: 'Harvest bare IDs' })).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(screen.getByRole('menuitem', { name: 'Delete' }));
    expect(remove).toHaveBeenCalledTimes(1);
    expect(edit).not.toHaveBeenCalled();
  });
});
