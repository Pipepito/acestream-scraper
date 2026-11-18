import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import CategoryArtwork from '../components/CategoryArtwork';
import ProgrammeArtwork from '../components/ProgrammeArtwork';
import { channelArtwork, programmeArtwork, sportArtwork } from '../artwork/categoryArtwork';

describe('Artwork metadata boundaries', () => {
  it.each([
    { values: [null, '0', 'unseen category'], expected: 'neutral' },
    { values: ['0', 'News / Current affairs'], expected: 'news' },
    { values: ['Sports', 'Football / Soccer'], expected: 'football' },
    { values: ['Tennis / Squash'], expected: 'sports-general' },
    { values: ['American Football', 'Football / Soccer'], expected: 'sports-general' },
    { values: ['Motor sport', 'Basketball'], expected: 'sports-general' },
    { values: ["Children's / Youth programs", 'Movie / Drama'], expected: 'children' },
    { values: ['Serious / Classical / Religious / Historical movie / Drama'], expected: 'film-drama' },
    { values: ['Music / Ballet / Dance', 'Arts / Culture (without music)'], expected: 'neutral' },
    { values: ['  cooking  '], expected: 'cooking' },
    { values: ['constructor'], expected: 'neutral' },
  ])('selects $expected for $values without splitting source labels', ({ values, expected }) => {
    expect(programmeArtwork(values)).toBe(expected);
  });

  it('keeps channel and event classifications separate from programme genres', () => {
    expect(channelArtwork('movies')).toBe('film-drama');
    expect(channelArtwork('Channel named Football')).toBe('neutral');
    expect(channelArtwork('constructor')).toBe('neutral');
    expect(channelArtwork('Movie / Drama')).toBe('neutral');
    expect(channelArtwork(null)).toBe('neutral');
    expect(sportArtwork('tennis')).toBe('tennis');
    expect(sportArtwork('F1')).toBe('motorsport');
    expect(sportArtwork('American Football')).toBe('sports-general');
    expect(sportArtwork('Tennis / Squash')).toBe('sports-general');
    expect(sportArtwork('')).toBeNull();
  });
});

describe('Decorative image resilience', () => {
  it('falls back once to neutral, then keeps the label and a solid unavailable state', () => {
    const { rerender } = render(<CategoryArtwork artwork="science" caption="Science category decoration" />);
    const illustration = screen.getByAltText('');
    expect(illustration).toHaveAttribute('loading', 'lazy');
    expect(illustration).toHaveAttribute('srcset', expect.stringContaining('-1280.webp 1280w'));
    fireEvent.error(illustration);
    expect(screen.getByAltText('')).toHaveAttribute('src', expect.stringContaining('neutral'));
    fireEvent.error(screen.getByAltText(''));
    expect(screen.getByText('Illustration unavailable')).toBeVisible();
    expect(screen.getByText('Science category decoration')).toBeVisible();
    expect(screen.queryByAltText('')).not.toBeInTheDocument();
    rerender(<CategoryArtwork artwork="cooking" caption="Cooking category decoration" />);
    expect(screen.getByAltText('')).toHaveAttribute('src', expect.stringContaining('cooking'));
  });

  it('shows real programme art before generic decoration and retries a new programme URL', () => {
    const fallback = <CategoryArtwork artwork="news" caption="Channel category decoration" />;
    const { rerender } = render(<ProgrammeArtwork src="https://example.test/first.webp" fallback={fallback} />);
    expect(screen.getByAltText('')).toHaveAttribute('src', 'https://example.test/first.webp');
    expect(screen.queryByText('Channel category decoration')).not.toBeInTheDocument();
    fireEvent.error(screen.getByAltText(''));
    expect(screen.getByText('Channel category decoration')).toBeVisible();
    rerender(<ProgrammeArtwork src="https://example.test/second.webp" fallback={fallback} />);
    expect(screen.getByAltText('')).toHaveAttribute('src', 'https://example.test/second.webp');
    expect(screen.queryByText('Channel category decoration')).not.toBeInTheDocument();
  });

  it.each([undefined, 'javascript:alert(1)', 'file:///private/image.png'])('uses local decoration for an absent or invalid source %s', src => {
    render(<ProgrammeArtwork src={src} fallback={<CategoryArtwork artwork="neutral" caption="Generic channel illustration" />} />);
    expect(screen.getByAltText('')).toHaveAttribute('src', expect.stringContaining('/static/visuals/tactile/ace-art-neutral'));
  });
});
