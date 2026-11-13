# Contrast correction evidence

Measured against the `2b55a46e` implementation plus the filled-primary contrast correction.
The original light-success defect persisted because `palette.success.main` used an icon color for ordinary text. Status text now uses its text token in light mode; dark mode keeps bright status colors. Filled controls have explicit contrasting text. Warning icons and destructive buttons were darkened. Input and outlined-button boundaries use a separate essential-control token; decorative panel dividers retain their softer border.

| Preset | Theme | Pairs | Lowest normal-text contrast | Lowest icon/control contrast |
|---|---|---:|---:|---:|
| coral | dark | 48 | 4.98:1 | 5.99:1 |
| coral | light | 48 | 5.38:1 | 3.68:1 |
| cyan | dark | 48 | 4.98:1 | 5.65:1 |
| cyan | light | 48 | 5.38:1 | 3.68:1 |
| lime | dark | 48 | 4.98:1 | 5.43:1 |
| lime | light | 48 | 5.38:1 | 3.68:1 |

Exact foreground/background colors, type roles and individual ratios are in [contrast-measurements.json](contrast-measurements.json). Body/helper text is 14 px at a standard 16 px root; the tests apply the stricter normal-text threshold regardless of larger headings. No disabled-control exception is counted as passing text contrast.

Reproduce with `UX_CONTRAST_REPORT=/tmp/ux-contrast npm --prefix frontend test -- --runInBand ThemeContrast.test.ts theme.test.tsx`. This exercises the actual theme factory for all three presets and both modes. It does not prove contrast over arbitrary programme images, browser rendering under every zoom/forced-color setting, or screen-reader behavior. Those remain separate browser/manual acceptance.

Before correction: the legacy light success `#1f8f59` on near-white was below 4.5:1; warning icon `#d97706` on `#fff4e5` was 2.93:1, destructive text `#fff7f7` on `#d14343` was 4.33:1, and light decorative border `#a7b5ab` on `#fbfefa` was 2.10:1. The latter remains suitable for decorative separation, but no longer defines interactive input/button boundaries.

A rendered axe check found that filled primary Chips used the link-colored palette background with the brighter primary-button text token. Coral/light measured 2.18:1 and cyan/light 2.03:1. Palette primary contrast now follows its own background; contained primary buttons retain their separate action tokens. The six-theme regression includes this pairing (288 total measurements).
