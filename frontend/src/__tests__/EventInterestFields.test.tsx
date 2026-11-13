import React, { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EventInterestFields from '../components/events/EventInterestFields';
import type { EventInterests } from '../services/eventService';

const choices: EventInterests = { sports: ['Basketball', 'Football'], competitions: ['COPA'], teams: [] };

function Harness({ initial, onOpen, ...props }: { initial?: EventInterests; onOpen?: () => void; choices?: EventInterests; allowCustom?: boolean; loading?: boolean }) {
  const [value, setValue] = useState<EventInterests>(initial ?? { sports: [], competitions: [], teams: [] });
  return <><EventInterestFields value={value} onChange={setValue} onOpen={onOpen} {...props} /><output>{JSON.stringify(value)}</output></>;
}
const saved = () => JSON.parse(screen.getByRole('status').textContent ?? '{}') as EventInterests;

it('offers the known names and never keeps one that was only typed', async () => {
  const user = userEvent.setup();
  const onOpen = jest.fn();
  render(<Harness choices={choices} onOpen={onOpen} />);
  expect(screen.getByText(/Choose from each list; type to find a name\./)).toBeVisible();
  const sports = screen.getByRole('combobox', { name: 'Sports' });
  await user.type(sports, 'Futbol{enter}');
  expect(onOpen).toHaveBeenCalled();
  expect(screen.getByText('No matching name')).toBeVisible();
  expect(saved().sports).toEqual([]);
  await user.clear(sports);
  // Case and accents do not matter while searching.
  await user.type(sports, 'FOOT');
  await user.click(screen.getByRole('option', { name: 'Football' }));
  expect(saved().sports).toEqual(['Football']);
});

it('keeps a name chosen earlier even when its source does not publish it now', async () => {
  const user = userEvent.setup();
  render(<Harness choices={choices} initial={{ sports: [], competitions: ['LIGA DE CAMPEONES'], teams: [] }} />);
  expect(screen.getByRole('button', { name: 'LIGA DE CAMPEONES' })).toBeVisible();
  await user.click(screen.getByRole('combobox', { name: 'Competitions' }));
  await user.click(screen.getByRole('option', { name: 'COPA' }));
  expect(saved().competitions).toEqual(['LIGA DE CAMPEONES', 'COPA']);
});

it('says when there is nothing to choose from, and while names are loading', async () => {
  const user = userEvent.setup();
  const { rerender } = render(<Harness loading />);
  await user.click(screen.getByRole('combobox', { name: 'Teams' }));
  expect(screen.getByText('Loading names…')).toBeVisible();
  rerender(<Harness />);
  expect(screen.getByText('No names to choose from yet')).toBeVisible();
});

it('lists at most the first hundred matches of a long list until typing narrows it', async () => {
  const user = userEvent.setup();
  const teams = Array.from({ length: 250 }, (_, index) => `Team ${String(index).padStart(3, '0')}`);
  render(<Harness choices={{ sports: [], competitions: [], teams }} />);
  const field = screen.getByRole('combobox', { name: 'Teams' });
  await user.click(field);
  expect(screen.getAllByRole('option')).toHaveLength(100);
  await user.type(field, '249');
  expect(screen.getAllByRole('option').map((option) => option.textContent)).toEqual(['Team 249']);
});

it('accepts typed names only where they cannot be listed beforehand', async () => {
  const user = userEvent.setup();
  render(<Harness allowCustom />);
  expect(screen.getByText(/Type each name exactly as the schedule spells it and press Enter\./)).toBeVisible();
  await user.type(screen.getByRole('combobox', { name: 'Sports' }), 'Football{enter}');
  expect(saved().sports).toEqual(['Football']);
});
