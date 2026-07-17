# Changelog

## V2.7.0 - 2026-07-17

- Adds selectable KanjiVG Original, Zen Kurenaido, Hachi Maru Pop, and Yomogi stroke styles in horizontal and vertical layouts.
- Keeps font-style packs as OFL-only skeleton derivatives and combines the separate KanjiVG/project-authored stroke-order layer only at runtime.
- Retains the base stroke count, order, and direction; missing or low-confidence style projections fall back to the KanjiVG/original path.
- Records each source font's original copyright, OFL text, pinned source commit, source version, SHA-256, converter and promotion records, glyph totals, fallback totals, and deterministic archive SHA-256.
- Documents that the three automatically converted centerline styles have limited character-by-character human review and must be checked in preview before use.
- Stores the selected stroke style in named presets while preserving compatibility with existing V2.6 settings.
- Remains unsigned; Windows SmartScreen may show an unknown-publisher warning.

## V2.6.2 - 2026-07-13

- Adds live crosshair guides, coordinates, and a three-second countdown while detecting start and end positions.
- Keeps the captured start position visible during end-coordinate detection and shows the planned writing rectangle when both points are on the same monitor.
- Replaces the opaque coordinate overlay with narrow native Windows guides so the target canvas remains visible during alignment.
- Fixes the coordinate-detection type error and the white or black full-screen overlay seen on some Windows systems.
- Synchronizes the validated special-symbol manifest with the corrected centerline SVG resources included in the portable package.
- Remains unsigned; Windows SmartScreen may show an unknown-publisher warning.

## V2.6.1 - 2026-07-13

- Adds standalone Traditional Chinese, English, and Japanese HTML complete guides that can be opened offline without a Markdown reader.
- Clarifies that only part of the Unicode special-symbol range is supported and that unsupported characters are reported before writing starts.
- Removes outdated help wording about built-in kaomoji categories and specific unsupported sequence types.
- Documents planned writing-font selection and continued special-symbol expansion.
- Keeps all V2.6.0 writing behavior and remains unsigned.

## V2.6.0 - 2026-07-12

- Modernizes the four-tab interface with a compact responsive layout, consistent icons, fixed primary actions, segmented direction controls, and visible numeric units.
- Adds light, dark, and Windows-following appearance modes; new and legacy settings without an appearance choice now start with the light theme.
- Preserves text, coordinates, presets, selected tab, window size, and maximized state while switching language or appearance.
- Improves preview clarity with dedicated start/end crosshairs, theme-aware canvas colors, writing-boundary styling, and operation status indicators.
- Adds Per-Monitor DPI awareness, Windows title-bar integration, a new application icon, and packaged UI resources.
- Keeps all V2.5.0 writing paths, layout behavior, emergency stopping, and portable settings compatible.
- Remains unsigned; Windows SmartScreen may show an unknown-publisher warning.

## V2.5.0 - 2026-07-11

- Writes user-entered kaomoji one character at a time with project-authored centerline SVG paths.
- Supports all 128 Unicode Box Drawing characters in `U+2500–U+257F`.
- Adds direct-codepoint resources for 89 common stars, geometric shapes, checks, arrows, brackets, and mathematical symbols.
- Preserves adaptive halfwidth/fullwidth spacing, halfwidth katakana composition, vertical layout, coordinate detection, presets, and emergency stopping.
- Rewrites the Traditional Chinese, English, and Japanese documentation for first-time users.
- Remains unsigned; Windows SmartScreen may show an unknown-publisher warning.
