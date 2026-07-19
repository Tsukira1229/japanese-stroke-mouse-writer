# Japanese Stroke Mouse Writer V2.7.1

V2.7.1 expands the writing-style system introduced after V2.6.2 while preserving the existing coordinate detection, layout, symbols, themes, and emergency-stop behavior.

## Highlights

- Adds Yomogi, Zen Kurenaido, and Hachi Maru Pop as selectable writing styles alongside KanjiVG.
- Includes locked best-effort drawing orders for 6,606 Yomogi, 6,591 Zen Kurenaido, and 6,608 Hachi Maru Pop catalog characters.
- Preserves every original centreline edge exactly once. These orders prioritize a complete visual result and do not guarantee authoritative Japanese stroke order.
- Falls back to KanjiVG for each style's documented unsupported glyphs, and falls back to the original centreline path order if order data is missing, damaged, or mismatched.
- Saves and restores the selected writing style in named presets.
- Renames the default option to `KanjiVG (Default)` and simplifies the three font-style names.

## Download

Download `JapaneseStrokeMouseWriter-v2.7.1-win-x64-portable.zip`, extract the complete folder, and run `JapaneseStrokeMouseWriter.exe`. No Python installation or administrator privileges are required.

This release is unsigned. Windows SmartScreen may show an unknown-publisher warning. Verify the included SHA-256 file before running the application.
