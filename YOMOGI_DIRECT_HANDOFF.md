# Yomogi Direct Centreline Handoff

## Scope and branch

- Feature branch: `codex/yomogi-direct-centerline`
- Base: `main` at `57466b8fe0b1d69090654f019511f16c181a300d` (V2.6.2 revert baseline)
- Application version is now `2.7.0` for the internal development build.
- This branch has not been merged, pushed, or published.
- The main task packages an uncompressed development folder at `build/development-v2.7.0/JapaneseStrokeMouseWriter-v2.7.0-development-win-x64-portable/`.
- No outer ZIP, release checksum, tag, or GitHub Release is created.

## Feature commits

1. `31349f1` — deterministic Yomogi converter, validator, provenance, fallback records, and formal style pack.
2. `0e7fc9f` — direct runtime loader, fixed 109 x 109 source cell, settings/CLI compatibility, and runtime tests.
3. `52dc010` — UI selection, four-language notices, user documentation, policy, and UI/document tests.

The handoff document is recorded in the following documentation-only commit.

## Delivered data

- KanjiVG catalog entries examined: 6,702
- Direct Yomogi SVGs for catalog entries: 6,606
- Additional approved Yomogi-only kana: 2 (`U+309F`, `U+30FF`)
- Total SVG members in `strokes.zip`: 6,608
- Explicit catalog fallbacks to KanjiVG: 96
  - Yomogi source-font missing: 87
  - Conversion-ineligible: 9
- Locked human-approved geometry: 191 (181 kana and 10 kanji)
- Human-approved kanji present in the pack: `U+4ED7`, `U+52A9`, `U+5340`, `U+59CB`, `U+5B73`, `U+5F97`, `U+6167`, `U+6483`, `U+6DD2`, `U+9F8D`
- Hard geometry failures: 0
- Missing source components among generated glyphs: 0
- Minimum 1.5-unit skeleton coverage: 0.993014
- All dense samples within the Yomogi shape or its 0.5-unit neighbourhood: yes
- Review-priority, non-blocking glyphs: 19
- Total paths: 70,175
- Total points: 255,115

`U+6549` and `U+64CA` were reviewed earlier but are absent from both the pinned Yomogi source and the current KanjiVG catalog, so they are not part of the 191 locked generated glyphs.

## Source and artifact hashes

- Yomogi Regular 3.100 commit: `2dcc1a21e9ee7cb66606d0be9099752504efe559`
- Yomogi source SHA-256: `3424e34bb951e89bf5dd2554a65d8964335ea3c0560f8d1ea9aa3591ef73cba9`
- `data/stroke_styles/yomogi/strokes.zip` SHA-256: `64969ec274424e3f0f2a9cce9208c1a7d5102f878ebf4ce1c4cd31cdabec40c6`
- Local portable verification ZIP SHA-256: `3d8960160abd2f1649c91895804056fd513a3403ae435715aa3e72f2e1cae1e4`

The formal pack contains `OFL.txt`, original copyright and source version in `SOURCE.md`, the conversion record in `manifest.json`, deterministic `strokes.zip`, and the exact 96-codepoint fallback list in JSON and CSV.

## Runtime behavior

- The UI exposes only KanjiVG Original and Yomogi Direct Centreline.
- Yomogi SVG paths are loaded and resampled directly. No KanjiVG geometry projection is present.
- Yomogi uses a fixed `0 0 109 109` source cell in horizontal and vertical layouts, preview, and real drawing.
- Only manifest-listed fallback characters and existing project custom symbols use KanjiVG/custom resources.
- Missing expected Yomogi archive members, including the two style-only kana, raise a style-resource error.
- Legacy settings and unknown saved style IDs normalize safely to KanjiVG.
- `GeneralSettings.stroke_style` and CLI `--stroke-style` are available.
- The UI notice states that Yomogi path order is visual and does not represent traditional stroke order, and that some characters fall back to KanjiVG.

## Validation performed

All commands were run from the repository root:

```powershell
python scripts/validate_yomogi_direct_style_pack.py
python scripts/validate_yomogi_direct_style_pack.py --reproduce
python -m unittest discover -s tests -v
python -m py_compile mouse_writer_pro.py mouse_writer_ui.pyw settings_store.py stroke_styles.py scripts/yomogi_direct_centerline.py scripts/generate_yomogi_direct_style_pack.py scripts/validate_yomogi_direct_style_pack.py
python scripts/generate_html_guides.py --check
python mouse_writer_ui.pyw --self-test --settings-path build/yomogi-direct-selftest/settings.json
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_portable.ps1
```

Results:

- Formal style validator: passed.
- Independent regeneration: passed with `reproducible=true`; SVG, ZIP, CSV, JSON, review images, and recorded hashes matched.
- Unit/UI/document suite: 136 tests passed.
- Source self-test: passed.
- PyInstaller portable build: passed.
- Frozen executable self-test before archiving: passed.
- Extracted portable executable self-test: passed.
- Bundled Yomogi `strokes.zip` hash equals the formal pack hash.

## Review artifacts

- Locked 191-glyph overview: `build/glyph-proof-yomogi-direct-full/review/approved-191.png`
- Nineteen review-priority glyphs: `build/glyph-proof-yomogi-direct-full/review/priority-flags.png`
- Full metrics and artifact hashes: `build/glyph-proof-yomogi-direct-full/metrics.json` and `artifact_hashes.json`

## Main-task checklist

1. Review this branch and the three feature commits plus the handoff commit.
2. V2.7.0 is assigned to the uncompressed internal development build; withdrawn release artifacts are not reused.
3. Review the uncompressed development folder and Yomogi paths before deciding whether to merge or publish.
4. If accepted later, rebuild any release artifact from the reviewed commit rather than reusing the development folder.
5. Publish only after the main task completes a separate release review.
