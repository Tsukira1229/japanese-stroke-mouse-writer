# Japanese Stroke Mouse Writer V2.1.2 Portable

[繁體中文](README.md) | English | [日本語](README.ja.md)

A portable stroke-order writing tool for Windows 10/11 x64. It uses Windows SendInput to write Japanese, English letters, numbers, and common symbols along centerline stroke paths in Paint or another canvas application.

## Installation

1. Download `JapaneseStrokeMouseWriter-v2.1.2-win-x64-portable.zip`.
2. Extract the entire ZIP to a writable folder.
3. Double-click `JapaneseStrokeMouseWriter.exe`.

Python and administrator privileges are not required. The program creates no installer or uninstaller entries. Settings are stored in `user_data/settings.json` beside the executable.

## Supported Content

- Japanese: hiragana, katakana, and KanjiVG-supported kanji.
- Small kana: contracted-sound kana, small tsu, small vowels, and other included small hiragana and katakana retain their reduced size.
- English: `A–Z` and `a–z`.
- Numbers: `0–9`.
- Symbols: `, . ! ? : ; 、。・ー ，～@`.
- Symbols retain their natural size and position within the cell; commas and periods remain near the bottom.
- Normal spaces, full-width spaces, tabs, and line breaks are preserved.

Unsupported characters or characters without stroke data are rejected before the mouse moves.

## Main Features

- Horizontal or vertical layout with left or right flow.
- Start/end coordinate detection, automatic wrapping, and bounds checking.
- Preview and mouse output share the same layout paths.
- Multiple named layout presets.
- Japanese, Traditional Chinese, Simplified Chinese, and English desktop UI.
- Global ESC emergency stop and screen-corner failsafe.

See the [complete guide](complete-guide.en.md) for operating instructions.

## Data Sources

Japanese, English, number, and selected symbol stroke data comes from [KanjiVG](https://kanjivg.tagaini.net/) ([GitHub](https://github.com/KanjiVG/kanjivg)) under CC BY-SA 3.0. The `～` and `@` centerline paths are project-authored. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

V2.1.2 is unsigned, so Windows SmartScreen may display an unknown-publisher warning.
