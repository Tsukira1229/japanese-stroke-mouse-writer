# Font-derived writing-style policy

Selectable font styles must be commercially usable, carry a redistributable license, and preserve their original copyright, license text, pinned source version, source hash, and conversion record.

## Yomogi direct centreline

- Source: Yomogi Regular 3.100, pinned commit and SHA-256 recorded in `data/stroke_styles/yomogi/SOURCE.md`.
- License: SIL Open Font License 1.1. The formal archive contains only geometry derived from Yomogi outlines.
- Runtime semantics: `visual-centerline`, `order=none`, `runtime-mode=direct`.
- KanjiVG is not used for Yomogi geometry, path order, direction, or path count. It remains a separate fallback resource for the 96 codepoints listed in `fallback.json`.
- A missing expected Yomogi archive member is treated as corruption. It must not silently fall back.
- Yomogi paths use the complete `0 0 109 109` source box so layout does not normalize each glyph by its path bounds.

## Promotion gates

- Every SVG must contain only non-empty M/L paths of at least 3 units.
- Source-component loss must be zero.
- Source-skeleton coverage within 1.5 units must be at least 99%.
- All dense path samples must remain inside the source outline or its 0.5-unit neighbourhood.
- The 191 manually approved glyphs are immutable at path-data level.
- Generator, archive, metrics, fallback data, and review artifacts must be deterministic before promotion.
