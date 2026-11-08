import { statusEnglish } from './messages/status-en';
import { statusSpanish } from './messages/status-es';
import { errorEnglish } from './messages/errors-en';
import { errorSpanish } from './messages/errors-es';
import { runtimeEnglish } from './messages/runtime-en';
import { runtimeSpanish } from './messages/runtime-es';
import { uiEnglish } from './messages/en';
import { uiSpanish } from './messages/es';

export const en = {
  ui: uiEnglish,
  runtime: runtimeEnglish,
  errors: errorEnglish,
  status: statusEnglish,
  common: {
    watch: 'Watch', recordings: 'Recordings', events: 'Events', channels: 'Channels', connections: 'Connections', settings: 'Settings', system: 'System',
    sources: 'Sources', guide: 'Programme guide', streams: 'Advanced streams', search: 'Search', playlists: 'Playlists',
    interface: 'Interface', language: 'Language', theme: 'Theme', light: 'Light', dark: 'Dark',
    lime: 'Lime', coral: 'Coral / navy', cyan: 'Immersive',
    limeDescription: 'Compact rows and bold headings. More information at a glance.',
    coralDescription: 'Warm surfaces and editorial layouts. A balanced view.',
    cyanDescription: 'Generous viewing layouts and larger imagery. Room to explore.',
    selected: 'Selected', chooseInterface: 'Choose your interface', close: 'Close', cancel: 'Cancel', save: 'Save', retry: 'Retry',
    preferenceError: 'Your preferences work for this visit, but could not be remembered in this browser.',
    preferenceReadError: 'Saved preferences could not be read. You can keep using the app and try again.',
    saving: 'Saving…', loading: 'Loading…', signOut: 'Sign out', skipContent: 'Skip to content',
    loadingPage: 'Loading page…', pageFailed: 'This page could not load. Your other pages and saved data are still available.',
    openNavigation: 'Open navigation', closeNavigation: 'Close navigation', navigation: 'Main navigation',
    tvChannels: 'TV channels', addChannels: 'Add channels', allChannels: 'All channels',
    thisBrowser: 'This browser', tvsPlayers: 'TVs and players', mediaServers: 'Media servers',
    publicAddress: 'Public address', notifications: 'Notifications', remotePlayers: 'Remote players',
    access: 'Access', automation: 'Automation', streamLinks: 'Stream links', runtime: 'Advanced connection settings',
    jobs: 'Scheduled jobs', storage: 'Storage', diagnostics: 'Diagnostics', changelog: 'What’s new',
    items_one: '{{count}} item', items_other: '{{count}} items',
  },
} as const;

type TranslationShape<T> = { [K in keyof T]: T[K] extends string ? string : TranslationShape<T[K]> };
export const es: TranslationShape<Omit<typeof en, 'ui'>> & { ui: typeof uiSpanish } = {
  ui: uiSpanish,
  runtime: runtimeSpanish,
  errors: errorSpanish,
  status: statusSpanish,
  common: {
    watch: 'Ver', recordings: 'Grabaciones', events: 'Eventos', channels: 'Canales', connections: 'Conexiones', settings: 'Ajustes', system: 'Sistema',
    sources: 'Fuentes', guide: 'Guía de programación', streams: 'Emisiones avanzadas', search: 'Buscar', playlists: 'Listas de reproducción',
    interface: 'Interfaz', language: 'Idioma', theme: 'Tema', light: 'Claro', dark: 'Oscuro',
    lime: 'Lima', coral: 'Coral / azul marino', cyan: 'Inmersiva',
    limeDescription: 'Filas compactas y títulos destacados. Más información de un vistazo.',
    coralDescription: 'Tonos cálidos y composición editorial. Una vista equilibrada.',
    cyanDescription: 'Más espacio para ver contenido e imágenes más grandes. Explora a tu ritmo.',
    selected: 'Seleccionada', chooseInterface: 'Elige tu interfaz', close: 'Cerrar', cancel: 'Cancelar', save: 'Guardar', retry: 'Reintentar',
    preferenceError: 'Tus preferencias se aplican durante esta visita, pero no se han podido guardar en este navegador.',
    preferenceReadError: 'No se han podido leer las preferencias guardadas. Puedes seguir usando la aplicación y reintentarlo.',
    saving: 'Guardando…', loading: 'Cargando…', signOut: 'Cerrar sesión', skipContent: 'Saltar al contenido',
    loadingPage: 'Cargando página…', pageFailed: 'No se ha podido cargar esta página. Las demás páginas y tus datos guardados siguen disponibles.',
    openNavigation: 'Abrir navegación', closeNavigation: 'Cerrar navegación', navigation: 'Navegación principal',
    tvChannels: 'Canales de TV', addChannels: 'Añadir canales', allChannels: 'Todos los canales',
    thisBrowser: 'Este navegador', tvsPlayers: 'Televisores y reproductores', mediaServers: 'Servidores multimedia',
    publicAddress: 'Dirección pública', notifications: 'Notificaciones', remotePlayers: 'Reproductores externos',
    access: 'Acceso', automation: 'Automatización', streamLinks: 'Enlaces de emisión', runtime: 'Conexiones avanzadas',
    jobs: 'Tareas programadas', storage: 'Almacenamiento', diagnostics: 'Diagnóstico', changelog: 'Novedades',
    items_one: '{{count}} elemento', items_other: '{{count}} elementos',
  },
};

export type CommonLabel = Exclude<keyof typeof en.common, `items_${string}`>;
