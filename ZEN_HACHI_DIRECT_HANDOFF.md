# Zen Kurenaido and Hachi Maru Pop Direct Centreline Handoff

## Scope and branch

- Handoff branch: `codex/zen-hachi-direct-handoff`
- Branch point: `4488ec3` on the existing Yomogi direct-centreline feature branch.
- Original V2.6.2/main baseline: `57466b8fe0b1d69090654f019511f16c181a300d`.
- This branch includes the previously completed Yomogi work plus the two new reviewed style packs.
- No merge to `main`, push, tag, release, or publication was performed in this task.
- Version naming and final release policy remain the responsibility of the version-control task.

## New commits

1. `0cc4315` — formal Zen Kurenaido and Hachi Maru Pop packs, OFL/provenance, fallback records, exact human-review locks, promotion, and validation scripts.
2. `8a6c0b4` — manifest-driven UI exposure, four-style self-test, localized notices/errors, runtime/layout/settings tests.
3. `348bdcf` — Traditional Chinese, English, and Japanese documentation plus third-party notices.

This handoff document is recorded in the following documentation-only commit.

## Zen Kurenaido delivered data

- Source: Zen Kurenaido Regular, Version 1.001.
- Pinned commit: `2edac135aa83e34640ec569d1d27520c3400e9b7`.
- Source TTF SHA-256: `58b8d930d9fc10c8a5810c085bae378dacb98d0779073ee6d53d919f19ee6a4f`.
- License: SIL Open Font License 1.1; original copyright and full OFL are included.
- KanjiVG catalog examined: 6,702 characters.
- Direct SVGs: 6,591.
- Explicit KanjiVG fallbacks: 111 (88 source-font-missing, 23 conversion-ineligible).
- Unexpected hard failures: 0.
- Missing source components: 0.
- Minimum 1.5-unit skeleton coverage: 0.997589.
- Soft review flags in the complete scan: 56.
- Total paths / points: 79,300 / 262,596.
- Formal `strokes.zip` SHA-256: `be8bc959480909f88a203f817ba546314ec49b4b9282d6252885923413c0b3c5`.

## Hachi Maru Pop delivered data

- Source: Hachi Maru Pop Regular, Version 1.300.
- Pinned commit: `252adbcc5e3722bd514c424c4a4395127f18d73c`.
- Source TTF SHA-256: `78408910c8f1a2f174a279cbc1484b48b71780039eba3fe1be2bfcc5d4df3f98`.
- License: SIL Open Font License 1.1; original copyright and full OFL are included.
- KanjiVG catalog examined: 6,702 characters.
- Direct SVGs: 6,608.
- Explicit KanjiVG fallbacks: 94 (88 source-font-missing, 6 conversion-ineligible).
- Unexpected hard failures: 0.
- Missing source components: 0.
- Minimum 1.5-unit skeleton coverage: 0.993902.
- Soft review flags in the complete scan: 7.
- Total paths / points: 70,221 / 298,300.
- Formal `strokes.zip` SHA-256: `f532cad5a310239553db7252e0abaeaed4fcbd7df116e477948e6709027e223e`.

Hachi Maru Pop uses the corrected, non-clipping source box: 436 px canvas, 390 px font size, Y=182 anchor, and mandatory zero boundary contact. The earlier clipped geometry is superseded. `U+5340 區` was regenerated with the correction and manually approved before the full pack and random review were generated.

## Human review locks

Each formal pack contains `HUMAN_REVIEW.json` with 389 unique, exact `path d` locks:

- 179 complete kana.
- 10 requested kanji anchors.
- 200 fixed-seed random Han characters, excluding the preceding 189 approvals.

The random samples used Python seed `20260718` and were approved in full by the user. Zen's sample contained one non-blocking automatic flag and had minimum coverage 1.000000. Hachi's sample contained no automatic flags and had minimum coverage 0.995720. The promoter validates every locked path against the formal archive before writing a pack.

## Runtime behavior

- The style selector now contains KanjiVG Original, Yomogi Direct Centreline, Zen Kurenaido Direct Centreline, and Hachi Maru Pop Direct Centreline.
- Both new styles use the existing manifest-driven direct loader. Their SVGs are loaded and resampled without KanjiVG projection.
- All direct styles keep the complete `0 0 109 109` source cell in horizontal and vertical layouts, preview, and real drawing.
- Only manifest-listed fallback characters and existing project custom symbols use KanjiVG/custom resources.
- A missing expected archive member raises a style-specific resource error rather than silently falling back.
- Existing settings remain compatible; unknown style IDs still normalize to KanjiVG.
- Path order is visual only and does not represent traditional stroke order.

## Validation and local promotion reproduction

The formal packs, archive hashes, SVG contract, fallback lists, provenance, and 389 exact human-review locks can be validated from a clean checkout. The optional `--reproduce` step re-promotes the packs from the preserved local `build/glyph-proof-*` review workspace; those review work files are intentionally not committed, so that step is not a clean-checkout source reproduction.

Commands run from the repository root:

```powershell
python scripts/validate_reviewed_direct_style_packs.py --reproduce
python scripts/validate_yomogi_direct_style_pack.py
python scripts/generate_html_guides.py --check
python -m py_compile mouse_writer_pro.py mouse_writer_ui.pyw settings_store.py stroke_styles.py localization.py scripts/promote_reviewed_direct_style_packs.py scripts/validate_reviewed_direct_style_packs.py
python -m unittest discover -s tests -v
python mouse_writer_ui.pyw --self-test --settings-path build/zen-hachi-handoff-selftest/settings.json
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_development_portable.ps1
```

Results on the handoff workstation:

- Both formal packs passed full SVG contract, fallback, provenance, archive hash, and all 389 human-lock comparisons.
- Local deterministic promotion reproduction passed; every formal file hash matched. This result depends on the preserved untracked review workspace described above.
- Existing Yomogi validator passed unchanged.
- Complete test suite: 140 tests passed.
- Source self-test: passed.
- PyInstaller uncompressed development build: passed.
- Frozen executable self-test: passed.
- Bundled Yomogi, Zen Kurenaido, and Hachi Maru Pop archive hashes equal their formal source hashes.

## Version-control review follow-up

The version-control review corrected three delivery-only inconsistencies without changing any stroke geometry:

- The development build now compares the bundled archive hash for all three direct styles, not only Yomogi.
- The Zen Kurenaido and Hachi Maru Pop quality aggregates now report the same 389 reviewed geometry locks as their conversion records and `HUMAN_REVIEW.json` files.
- The optional reproduction command now reports clearly that it requires the preserved local review workspace.

After these corrections, all 140 tests, source and frozen self-tests, local promotion reproduction, and the three packaged archive hash comparisons passed. The branch remains a development candidate and requires real drawing acceptance before merge or release.

Local build for optional main-task inspection:

`build/development-v2.7.0/JapaneseStrokeMouseWriter-v2.7.0-development-win-x64-portable/`

This folder is a local, uncompressed development artifact. It is not a release and must not be reused as a future release package without a fresh build and release review.

## Main-task checklist

1. Read this file and `YOMOGI_DIRECT_HANDOFF.md`.
2. Review commits `0cc4315`, `8a6c0b4`, `348bdcf`, and the handoff commit.
3. Decide whether to merge the entire branch or cherry-pick only the new four commits onto the version-control task's reviewed base.
4. Re-run the validation commands above in the target branch.
5. Decide the final version number and changelog in the version-control task.
6. Merge, push, tag, package, or publish only after the separate main-task review.
