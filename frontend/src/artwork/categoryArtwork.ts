import programmeCategories from './programme-category-map.json';

export const GENERATED_ARTWORK = [
  'film-drama', 'documentary', 'news', 'children', 'entertainment', 'music',
  'lifestyle', 'cooking', 'science', 'culture', 'travel', 'sports-general',
  'motorsport', 'neutral',
] as const;

export type ArtworkKey = typeof GENERATED_ARTWORK[number] | 'football' | 'tennis' | 'nature';

export interface ArtworkSource {
  src: string;
  srcSet?: string;
  width: number;
  height: number;
}

export function artworkSource(key: ArtworkKey): ArtworkSource {
  if (key === 'football') return {
    src: '/static/visuals/football-480.webp',
    srcSet: '/static/visuals/football-480.webp 480w, /static/visuals/football-960.webp 960w', width: 480, height: 322,
  };
  if (key === 'tennis') return { src: '/static/visuals/tennis-480.webp', width: 480, height: 360 };
  if (key === 'nature') return {
    src: '/static/visuals/coast-800.webp',
    srcSet: '/static/visuals/coast-800.webp 800w, /static/visuals/coast-1600.webp 1600w', width: 800, height: 451,
  };
  const base = `/static/visuals/tactile/ace-art-${key}-v1`;
  return { src: `${base}-640.webp`, srcSet: `${base}-320.webp 320w, ${base}-640.webp 640w, ${base}-1280.webp 1280w`, width: 640, height: 360 };
}

interface ProgrammeCategory {
  original: string;
  canonical_key: string;
  image_key: string;
  priority: number;
}

const artworkKeys = new Set<string>([...GENERATED_ARTWORK, 'football', 'tennis', 'nature']);
const isArtworkKey = (value: string): value is ArtworkKey => artworkKeys.has(value);
/** The taxonomy can gain categories before their artwork exists. */
export const resolvedArtwork = (value: string): ArtworkKey => isArtworkKey(value) ? value : 'neutral';
const exactCategories = new Map<string, ProgrammeCategory>(programmeCategories.map(entry => [entry.original, entry]));
const normalize = (value: string): string => value.normalize('NFC').trim().toLocaleLowerCase('en');
const normalizedCategories = new Map<string, ProgrammeCategory | null>();
for (const entry of programmeCategories) {
  const key = normalize(entry.original);
  const previous = normalizedCategories.get(key);
  normalizedCategories.set(key, previous === null || (previous && (previous.canonical_key !== entry.canonical_key || previous.image_key !== entry.image_key || previous.priority !== entry.priority)) ? null : entry);
}

/** Lookup only: preserve source strings and treat compound XMLTV labels as indivisible. */
export function programmeArtwork(categories: readonly (string | null | undefined)[]): ArtworkKey {
  const choices = categories.flatMap(value => {
    if (!value) return [];
    const entry = exactCategories.get(value) ?? normalizedCategories.get(normalize(value));
    return entry && entry.priority > 0 ? [entry] : [];
  });
  if (!choices.length) return 'neutral';
  const priority = Math.max(...choices.map(entry => entry.priority));
  const winners = choices.filter(entry => entry.priority === priority);
  const sports = new Set(['sports-general', 'football', 'tennis', 'motorsport']);
  if (new Set(winners.map(entry => entry.canonical_key)).size > 1 && winners.every(entry => sports.has(entry.image_key))) return 'sports-general';
  const images = new Set(winners.map(entry => entry.image_key));
  const image = winners[0].image_key;
  return images.size === 1 && isArtworkKey(image) ? image : 'neutral';
}

// Channel identity is a separate taxonomy: never infer it from the current show or name.
const channelAliases = new Map<string, ArtworkKey>(Object.entries({
  movies: 'film-drama', films: 'film-drama', cinema: 'film-drama', cine: 'film-drama', series: 'film-drama',
  documentary: 'documentary', documentaries: 'documentary', documentales: 'documentary',
  news: 'news', noticias: 'news', 'current affairs': 'news',
  kids: 'children', children: 'children', infantil: 'children', infantiles: 'children',
  entertainment: 'entertainment', entretenimiento: 'entertainment',
  music: 'music', música: 'music', musica: 'music', lifestyle: 'lifestyle', 'estilo de vida': 'lifestyle',
  cooking: 'cooking', cocina: 'cooking', science: 'science', ciencia: 'science', education: 'science', educación: 'science',
  culture: 'culture', cultura: 'culture', travel: 'travel', viajes: 'travel', nature: 'nature', naturaleza: 'nature',
  sports: 'sports-general', deportes: 'sports-general', sport: 'sports-general',
  football: 'football', soccer: 'football', fútbol: 'football', futbol: 'football',
  tennis: 'tennis', tenis: 'tennis', motorsport: 'motorsport', 'motor sport': 'motorsport',
} satisfies Record<string, ArtworkKey>));

export function channelArtwork(category?: string | null): ArtworkKey {
  return category ? channelAliases.get(normalize(category)) ?? 'neutral' : 'neutral';
}

/** Event sport metadata only. Unknown disciplines stay neutral rather than becoming football. */
export function sportArtwork(sport?: string | null): ArtworkKey | null {
  if (!sport?.trim()) return null;
  const name = normalize(sport);
  const exact = channelAliases.get(name);
  if (exact && ['football', 'tennis', 'motorsport', 'sports-general'].includes(exact)) return exact;
  if (['formula 1', 'formula one', 'f1', 'motogp', 'moto gp', 'motor racing'].includes(name)) return 'motorsport';
  const entry = exactCategories.get(sport) ?? normalizedCategories.get(name);
  if (entry && ['football', 'tennis', 'motorsport', 'sports-general'].includes(entry.image_key) && isArtworkKey(entry.image_key)) return entry.image_key;
  // A nonempty event sport is evidence of sport, not of a particular discipline.
  return 'sports-general';
}
