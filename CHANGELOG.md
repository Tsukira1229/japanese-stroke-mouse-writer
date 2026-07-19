# Changelog

## V2.7.1 Development - 2026-07-19

- Adds locked best-effort drawing-order sidecars for 6,606 Yomogi, 6,591 Zen Kurenaido, and 6,608 Hachi Maru Pop catalog characters.
- Preserves every original centreline edge exactly once and safely falls back to each SVG's original path order if sidecar data is missing, damaged, or mismatched.
- Renames the writing-style choices to KanjiVG (Default), Yomogi, Zen Kurenaido, and Hachi Maru Pop.
- Locks named presets to save and restore the selected writing style together with the existing layout settings.
- Remains an unsigned, uncompressed internal development build; no GitHub Release is created.

## V2.7.0 Development - 2026-07-18

- Adds a selectable Yomogi Direct Centreline style as the internal V2.7.0 development build.
- Uses 6,608 font-derived direct SVGs and never projects KanjiVG geometry onto the font skeleton.
- Preserves 191 manually approved glyph geometries and reports 96 explicit KanjiVG fallbacks.
- Keeps KanjiVG as the default for legacy settings and unknown style identifiers.
- This build is kept as an uncompressed internal development folder; no tag, GitHub Release, or outer ZIP is created.

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
