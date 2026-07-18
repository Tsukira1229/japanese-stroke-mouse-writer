# Third-Party Notices

## KanjiVG

This application includes KanjiVG stroke-order SVG data.

- Project: https://kanjivg.tagaini.net/
- Repository: https://github.com/KanjiVG/kanjivg
- Version: 20250816
- License: Creative Commons Attribution-ShareAlike 3.0
- License text: https://creativecommons.org/licenses/by-sa/3.0/

KanjiVG data remains subject to its original attribution and share-alike terms.

## Yomogi

This feature branch includes centreline SVG data derived solely from Yomogi Regular 3.100 glyph shapes.

- Project: https://github.com/satsuyako/YomogiFont
- Pinned commit: `2dcc1a21e9ee7cb66606d0be9099752504efe559`
- Source SHA-256: `3424e34bb951e89bf5dd2554a65d8964335ea3c0560f8d1ea9aa3591ef73cba9`
- Copyright: Copyright 2020 The Yomogi Project Authors (https://github.com/satsuyako/YomogiFont), all rights reserved.
- License: SIL Open Font License 1.1

The Yomogi-derived centreline archive, original copyright, OFL text, conversion record, and fallback list are stored under `data/stroke_styles/yomogi`. KanjiVG geometry is not included in that OFL archive. At runtime, 96 explicitly listed catalog characters use the separately bundled KanjiVG resource.

## Zen Kurenaido

This feature branch includes centreline SVG data derived solely from Zen Kurenaido Regular 1.001 glyph shapes.

- Project: https://github.com/googlefonts/zen-kurenaido
- Pinned commit: `2edac135aa83e34640ec569d1d27520c3400e9b7`
- Source SHA-256: `58b8d930d9fc10c8a5810c085bae378dacb98d0779073ee6d53d919f19ee6a4f`
- Copyright: Copyright 2021 The Zen Kurenaido Project Authors (https://github.com/googlefonts/zen-kurenaido)
- License: SIL Open Font License 1.1

The derived archive, exact 389-glyph human-review lock, OFL text, source record, and 111-character fallback list are stored under `data/stroke_styles/zen-kurenaido`.

## Hachi Maru Pop

This feature branch includes centreline SVG data derived solely from Hachi Maru Pop Regular 1.300 glyph shapes.

- Project: https://github.com/noriokanisawa/HachiMaruPop
- Pinned commit: `252adbcc5e3722bd514c424c4a4395127f18d73c`
- Source SHA-256: `78408910c8f1a2f174a279cbc1484b48b71780039eba3fe1be2bfcc5d4df3f98`
- Copyright: Copyright 2020 The Hachi Maru Pop Project Authors (https://github.com/noriokanisawa/HachiMaruPop)
- License: SIL Open Font License 1.1

The derived archive, exact 389-glyph human-review lock, OFL text, source record, and 94-character fallback list are stored under `data/stroke_styles/hachi-maru-pop`. Hachi Maru Pop uses its corrected 390 px source render with Y=182 anchoring; boundary contact is rejected to prevent clipped glyphs such as `區`.

## Python dependencies

The Portable build includes open-source Python and Python packages. Direct project dependencies include:

- Python: Python Software Foundation License
- matplotlib: Matplotlib License
- PyAutoGUI: BSD 3-Clause License
- svg.path: MIT License
- ttkbootstrap: MIT License
- PyInstaller: GNU GPL with the PyInstaller bootloader exception
- Python-Markdown: BSD 3-Clause License (build-time HTML documentation generation)
- fontTools: MIT License (build-time font inspection)
- NumPy: BSD 3-Clause License (build-time centreline conversion)
- Pillow: HPND License (build-time glyph rasterization)
- scikit-image: BSD 3-Clause License (build-time skeletonization)
- SciPy: BSD 3-Clause License (build-time geometry validation)

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
