# Third-Party Notices

## KanjiVG

This application includes KanjiVG stroke-order SVG data.

- Project: https://kanjivg.tagaini.net/
- Repository: https://github.com/KanjiVG/kanjivg
- Version: 20250816
- License: Creative Commons Attribution-ShareAlike 3.0
- License text: https://creativecommons.org/licenses/by-sa/3.0/

KanjiVG data remains subject to its original attribution and share-alike terms.

## Python dependencies

The Portable build includes open-source Python and Python packages. Direct project dependencies include:

- Python: Python Software Foundation License
- matplotlib: Matplotlib License
- PyAutoGUI: BSD 3-Clause License
- svg.path: MIT License
- ttkbootstrap: MIT License
- PyInstaller: GNU GPL with the PyInstaller bootloader exception

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
