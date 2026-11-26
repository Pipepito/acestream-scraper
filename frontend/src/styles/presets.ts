import type { AppTokens } from '../theme.d';
import type { InterfaceId } from '../preferences/AppPreferences';

export const presetPalettes = {
  lime: { light: ['#f3f4ed', '#fdfef6', '#242d22', '#4c5948'], dark: ['#1a2119', '#252e22', '#f5faeb', '#c1cdb8'], accent: '#c0ef54', ink: '#222d16', link: '#425b16', radius: 3, spacing: 2.25 },
  coral: { light: ['#f6f3ee', '#fffcf7', '#202336', '#575969'], dark: ['#151827', '#202435', '#faf6ef', '#c7c6d2'], accent: '#ffad87', ink: '#202336', link: '#953d1b', radius: 10, spacing: 3 },
  cyan: { light: ['#f0f5f2', '#fbfefa', '#142b2b', '#49605b'], dark: ['#101f21', '#192c2e', '#eff9f2', '#b7ccc5'], accent: '#55dfc4', ink: '#102e29', link: '#146352', radius: 14, spacing: 3.5 },
} as const;

/** Presentation only: domain state, service calls and permissions never enter here. */
export function applyPreset(base: AppTokens, mode: 'light' | 'dark', id: InterfaceId): AppTokens {
  const preset = presetPalettes[id];
  const [canvas, panel, text, muted] = preset[mode];
  const border = mode === 'light' ? '#a7b5ab' : '#667c73';
  const link = mode === 'light' ? preset.link : preset.accent;
  return {
    ...base,
    surface: { canvas, panel, muted: canvas, raised: panel, border },
    text: { primary: text, secondary: muted, muted, inverse: preset.ink },
    shell: { navBg: panel, navBorder: border, appBarBg: panel, appBarBorder: border, accent: preset.accent,
      activeNavBg: preset.accent, activeNavText: preset.ink, activeNavBorder: preset.ink, contentGlow: 'none' },
    hero: { bg: panel, border, accent: preset.accent, muted: canvas, spotlight: 'none' },
    action: { ...base.action, primaryBg: preset.accent, primaryHover: id === 'lime' ? '#a8d63f' : id === 'coral' ? '#f3976c' : '#35c8ac',
      primaryText: preset.ink, secondaryBg: canvas, secondaryText: link, focusRing: link, accentWarm: preset.accent },
    layout: { ...base.layout, sectionGap: preset.spacing, panelPadding: preset.spacing,
      cardRadius: preset.radius, divider: border, elevatedShadow: 'none',
      shell: { ...base.layout.shell, navWidth: id === 'lime' ? 232 : 252 } },
  };
}
