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
