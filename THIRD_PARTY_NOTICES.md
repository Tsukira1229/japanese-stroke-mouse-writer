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
- PyInstaller: GNU GPL with the PyInstaller bootloader exception

These packages may include transitive open-source dependencies under their respective licenses. Their original copyright and license terms remain in effect.

## Project-authored stroke data

The centerline SVG paths for U+FF5E FULLWIDTH TILDE (`～`), U+0040 COMMERCIAL AT (`@`), the Japanese brackets `「」『』【】〈〉《》〔〕`, and the following 24 ASCII punctuation characters were created specifically for this project and are not third-party data:

```text
" # $ % & ' ( ) * + - / < = > [ \\ ] ^ _ ` { | }
```

Fullwidth aliases use the corresponding ASCII source path. Project-authored stroke data is licensed under the project MIT License. Characters that resolve to included KanjiVG paths remain subject to the KanjiVG terms above.
