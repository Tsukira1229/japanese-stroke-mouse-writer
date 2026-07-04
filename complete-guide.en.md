# Japanese Stroke Mouse Writer V2.3.0 Complete Guide

[繁體中文](complete-guide.md) | English | [日本語](complete-guide.ja.md)

## 1. Open the Program

Extract the entire Portable ZIP, then double-click `JapaneseStrokeMouseWriter.exe`. It starts maximized, with the emergency-stop hint in the bottom status bar. The in-app Help tab also contains the operating instructions. Do not run it from the ZIP preview or place it in a protected system folder.

## 2. Enter Content and Preview

Enter Japanese, English letters, numbers, or supported symbols in Content & Preview. The editor preserves layout: a normal space uses `0.5` cell, a fullwidth space uses `1` cell, and Tab displays four half-cells occupying `2` cells. Enter starts a new row or column, and repeated line breaks are retained.

English letters and numbers support both halfwidth and fullwidth forms of `A–Z`, `a–z`, and `0–9`. Halfwidth katakana occupies `0.5` cell, and voiced combinations such as `ｶﾞ` and `ﾊﾟ` become one half-cell glyph. Symbol pairs include `#＃ (（ )） [［ ]］ @＠ ~～ 、､ 。｡ ・･ ーｰ`, plus `「」『』【】〈〉《》〔〕｢｣`. Unicode halfwidth/narrow characters occupy `0.5` cell, while fullwidth/wide characters occupy `1` cell; paired forms share stroke data. Included contracted-sound kana, small tsu, and small vowels retain their reduced size. Other characters produce an error before writing. Light cells show actual layout occupancy; black lines show stroke paths.

## 3. Detect the Canvas Bounds

1. Open the target canvas and select a pencil or brush.
2. Click Detect start coordinates.
3. For right flow, select the top-left corner; for left flow, select the top-right corner.
4. Click Detect end coordinates and select the opposite edge of the writable area.

Press ESC during detection to cancel. Coordinates can also be entered manually and may be negative on multi-monitor desktops.

## 4. General Settings

- Font size: width and height of each character cell in pixels.
- Character/line gap: spacing between cells and wrapped rows or columns.
- Orientation: horizontal or vertical.
- Flow: right or left.

Horizontal text wraps downward at the side boundary. Vertical text creates a new left or right column at the bottom boundary. In vertical layout, letters, numbers, brackets, and long marks rotate clockwise, while `、。` move to the upper-right corner.

### Presets

Add, load, overwrite, rename, or delete named layout presets. Presets save font size, gaps, orientation, and flow, but not text or coordinates.

## 5. Environment Settings

- Language: Japanese, Traditional Chinese, Simplified Chinese, or English; changes apply immediately.
- Start countdown: `0–30` seconds.
- Curve detail: `0.1–20`; smaller values are smoother but slower.
- Sample delay: `1–1000` ms; increase it if strokes break.

Numeric controls normalize full-width digits and common decimal separators.

## 6. Start and Stop Writing

After checking the preview, click Start writing. Every character, resource, and canvas bound is validated before the mouse moves. Press ESC during writing or move the pointer to a screen corner to stop.

## 7. Troubleshooting

- **Unsupported writing character**: use Japanese, letters, numbers, or symbols listed in the README.
- **Only straight lines appear**: select a pencil or brush instead of a line or shape tool.
- **Canvas overflow**: enlarge the bounds, reduce font size, or reduce gaps.
- **Folder is not writable**: move the whole program folder to Desktop, Documents, or another writable location.
- **SmartScreen warning**: V2.3.0 is unsigned; download it from the official Release and verify SHA-256.
