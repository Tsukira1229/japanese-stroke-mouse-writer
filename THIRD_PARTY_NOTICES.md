# Third-Party Notices

## KanjiVG

This application includes KanjiVG stroke-order SVG data.

- Project: https://kanjivg.tagaini.net/
- Repository: https://github.com/KanjiVG/kanjivg
- Version: 20250816
- License: Creative Commons Attribution-ShareAlike 3.0
- License text: https://creativecommons.org/licenses/by-sa/3.0/

KanjiVG data remains subject to its original attribution and share-alike terms.

## OFL font-style packs

V2.7.0 includes three font-skeleton style packs. Each pack contains `manifest.json`, the original `OFL.txt`, `SOURCE.md`, and a deterministic `strokes.zip`. The archive contains only centerline skeletons derived from the named font outline; it does not contain KanjiVG geometry or stroke order. At runtime, the application loads the KanjiVG/project-authored stroke layer separately and fits it to the selected skeleton. This separation keeps the reusable font-style pack under its source SIL Open Font License 1.1 while retaining the independent license of the base stroke data.

### Zen Kurenaido Regular

- Original copyright: Copyright 2021 The Zen Kurenaido Project Authors (https://github.com/googlefonts/zen-kurenaido)
- Source version: Version 1.001
- Pinned source commit: `2edac135aa83e34640ec569d1d27520c3400e9b7`
- Source font SHA-256: `58b8d930d9fc10c8a5810c085bae378dacb98d0779073ee6d53d919f19ee6a4f`
- Derived archive SHA-256: `c97e1f5efe171dd01df4dd96fb0e7f1eb16d9e36c2a0b1f7f24ec03b87670b83`
- License: SIL Open Font License 1.1, included at `data/stroke_styles/zen-kurenaido/OFL.txt`
- Conversion record: `data/stroke_styles/zen-kurenaido/SOURCE.md`

### Hachi Maru Pop Regular

- Original copyright: Copyright 2020 The Hachi Maru Pop Project Authors (https://github.com/noriokanisawa/HachiMaruPop)
- Source version: Version 1.300
- Pinned source commit: `252adbcc5e3722bd514c424c4a4395127f18d73c`
- Source font SHA-256: `78408910c8f1a2f174a279cbc1484b48b71780039eba3fe1be2bfcc5d4df3f98`
- Derived archive SHA-256: `69f92d37a0a3711ccd0cf1ae9d28be02a5246c6f1749cc2a11c453da0b21f065`
- License: SIL Open Font License 1.1, included at `data/stroke_styles/hachi-maru-pop/OFL.txt`
- Conversion record: `data/stroke_styles/hachi-maru-pop/SOURCE.md`

### Yomogi Regular

- Original copyright: Copyright 2020 The Yomogi Project Authors (https://github.com/satsuyako/YomogiFont), all rights reserved.
- Source version: Version 3.100
- Pinned source commit: `2dcc1a21e9ee7cb66606d0be9099752504efe559`
- Source font SHA-256: `3424e34bb951e89bf5dd2554a65d8964335ea3c0560f8d1ea9aa3591ef73cba9`
- Derived archive SHA-256: `073f83a6f6351f3d1c7400cd4253473a5ec21a22d787ca0fa98156781205812d`
- License: SIL Open Font License 1.1, included at `data/stroke_styles/yomogi/OFL.txt`
- Conversion record: `data/stroke_styles/yomogi/SOURCE.md`

The complete, machine-readable source repository, pinned commit, source SHA-256, original copyright, conversion and promotion records, glyph counts, fallback count, review status, and derived archive SHA-256 are retained in each manifest. These style packs are approximate single-line writing data and are not replacements for the original outline fonts.

## Python dependencies

The Portable build includes open-source Python and Python packages. Direct project dependencies include:

- Python: Python Software Foundation License
- matplotlib: Matplotlib License
- PyAutoGUI: BSD 3-Clause License
- svg.path: MIT License
- ttkbootstrap: MIT License
- PyInstaller: GNU GPL with the PyInstaller bootloader exception
- Python-Markdown: BSD 3-Clause License (build-time HTML documentation generation)
- fontTools: MIT License (build-time source-font metadata inspection)
- Pillow: HPND License (build-time font rasterization)
- NumPy: BSD 3-Clause License (build-time geometry processing)
- scikit-image: BSD 3-Clause License (build-time skeletonization)

These packages may include transitive open-source dependencies under their respective licenses. Their original copyright and license terms remain in effect.

## Project-authored stroke data

The centerline SVG paths for U+FF5E FULLWIDTH TILDE (`～`), U+0040 COMMERCIAL AT (`@`), the Japanese brackets `「」『』【】〈〉《》〔〕`, and the following 24 ASCII punctuation characters were created specifically for this project and are not third-party data:

```text
" # $ % & ' ( ) * + - / < = > [ \\ ] ^ _ ` { | }
```

Fullwidth aliases use the corresponding ASCII source path. Project-authored stroke data is licensed under the project MIT License. Characters that resolve to included KanjiVG paths remain subject to the KanjiVG terms above.

V2.5.0 and later include project-authored centerline SVG paths for selected Unicode symbols that are useful when users manually assemble kaomoji and line drawings. These paths are not copied from third-party symbol lists and are licensed under the project MIT License.

## Lucide icons

The interface includes selected icons from [Lucide](https://lucide.dev/), used under the ISC License. The original SVG source files and generated light/dark PNG assets are included under `data/ui/icons`.
