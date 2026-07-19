# Japanese Stroke Mouse Writer V2.7.1 Development Complete Guide

This guide starts with the first launch and explains how to define the writing area, verify the preview, and run the program safely.

## 1. Launch and Prepare the Canvas

1. Run `JapaneseStrokeMouseWriter.exe`. The window opens maximized. Its initial language follows Windows and can be changed in **Environment Settings**.
2. Open Paint or another application that accepts mouse drawing.
3. Select the target pen or pencil tool and set its color and thickness.
4. Make sure the canvas is large enough and no dialog or window covers the intended writing area.

## 2. Enter the Writing Content

Enter or paste text in **Content & Preview**. Spaces, Tab, explicit line breaks, and repeated line breaks are preserved. Text without a manual line break wraps automatically when it reaches the main boundary of the writable rectangle.

You can type kaomoji directly, such as `(^O^)`, `(≧▽≦)`, `m(_ _)m`, `(/ω＼)`, and `(╯°□°)╯︵ ┻━┻`. A kaomoji is assembled from the centerline paths of its individual supported characters, so symbol choice, halfwidth/fullwidth forms, and spacing affect the result.

## 3. Set Start and End Coordinates

The start and end coordinates form the writable rectangle. They are X/Y pointer positions across the complete Windows desktop and may be negative on multi-monitor systems.

- Horizontal or vertical with right flow: Start is the top-left corner and End is the bottom-right corner.
- Horizontal or vertical with left flow: Start is the top-right corner and End is the bottom-left corner.

Coordinate detection is recommended:

1. Click **Detect start coordinates**. The main window minimizes, and the pointer's current monitor shows a crosshair, live X/Y coordinates, and a three-second countdown.
2. Move the crosshair intersection to the matching upper corner of the target canvas and hold it still. Moving the pointer to another monitor moves the crosshair there automatically.
3. Click **Detect end coordinates**, then move the pointer to the matching lower corner. The captured start remains marked. When both points are on the same monitor, the expected writing rectangle is shown live; otherwise, the start monitor retains its start crosshair and coordinates.
4. When the program returns, verify the captured X and Y values. Coordinates may also be entered manually.

Press `ESC` during detection to cancel without replacing the previous values. The rectangle must fit at least one character cell; invalid range or direction is reported before preview.

## 4. Adjust General Settings

- **Font size**: width and height of one fullwidth cell in px.
- **Character gap**: distance between adjacent characters. Two halfwidth characters use half this value; other pairs use the full value.
- **Line gap**: row spacing in horizontal layout or column spacing in vertical layout.
- **Orientation**: horizontal places characters left or right; vertical places characters downward.
- **Flow**: right or left, which also determines the side used by the start coordinate.
- **Writing style**: KanjiVG (Default) follows its source stroke order. Yomogi, Zen Kurenaido, and Hachi Maru Pop use locked best-effort drawing orders that preserve every original skeleton edge but do not guarantee authoritative Japanese stroke order. Invalid order data falls back to the original centreline path order.

Halfwidth characters occupy `0.5` cell, fullwidth and wide characters occupy `1` cell, and Tab equals four halfwidth spaces. Valid halfwidth katakana combinations such as `ｶﾞ` and `ﾊﾟ` occupy one half-cell.

In vertical layout, alphanumeric characters, brackets, and long marks rotate clockwise. `、。` move to the upper-right of their cells. Arrows and box-drawing characters preserve their direction.

**Presets** can add, load, overwrite, rename, or delete named settings. A preset stores font size, character gap, line gap, orientation, flow, and writing style; it does not store text or coordinates.

## 5. Adjust Environment Settings

- **Language**: Japanese, Traditional Chinese, Simplified Chinese, or English.
- **Appearance**: Light, dark, or follow Windows. The light theme is the default for first use.
- **Start countdown**: seconds available to switch to the target canvas after starting; range `0–30`.
- **Curve detail**: range `0.1–20`. Smaller values create smoother curves with more points and longer writing time.
- **Sample delay**: wait time at each curve point; range `1–1000` ms. Increase it gradually if strokes break.

Environment settings are saved automatically. Switching language or appearance preserves text, coordinates, the selected tab, and window state. Start with the defaults and adjust only when curves are rough or strokes break.

## 6. Check Supported Input

Supported input includes Japanese kana, kanji available in KanjiVG, `A–Z`, `a–z`, `0–9`, fullwidth alphanumerics, halfwidth katakana, and common symbols.

Yomogi provides 6,608 direct glyphs and 96 fallbacks, including the style-only kana `ゟ` and `ヿ`. Zen Kurenaido provides 6,591 direct glyphs and 111 fallbacks; Hachi Maru Pop provides 6,608 direct glyphs and 94 fallbacks. Fallback is limited to the source-missing or conversion-ineligible characters explicitly listed by each pack.

The three font styles provide 6,606, 6,591, and 6,608 best-effort drawing-order maps respectively. An order map only reorders, reverses, or splits at existing points, so every original skeleton edge is still used exactly once; this is not an authoritative Japanese stroke order. Missing, damaged, or source-mismatched order data automatically uses the original centreline path order. Named presets save and restore the selected writing style.

Halfwidth/fullwidth pairs include `#＃`, `(（`, `)）`, `[［`, `]］`, `@＠`, `~～`, `、､`, `。｡`, `・･`, `ーｰ`, `「」`, `【】`, and `｢｣`. The program also supports some commonly used geometry, stars, checks, arrows, brackets, mathematics, and box-drawing symbols. See [Supported Centerline Symbols](SUPPORTED_SYMBOLS.md) for the complete list.

Not every special symbol is available. If the text contains an unsupported special symbol, the first unsupported character is reported before writing starts.

For box drawing, set character gap and line gap to `0 px` to connect adjacent endpoints in `┏━┷━┓`, `┃　　┃`, and `┗━━━┛`.

## 7. Update the Preview

Click **Update preview**. Light cells show the occupied character areas, and black lines are the exact paths sent to the mouse.

Before starting, confirm that:

- All content is inside the writable rectangle.
- Spaces, explicit line breaks, and automatic wrapping appear as expected.
- Filled symbols have the required outer boundary and sparse diagonal hatching.
- No unsupported-character or insufficient-range warning is shown.

## 8. Start Writing and Stop Safely

1. Click **Start writing**.
2. Switch to the target canvas during the countdown. Do not move the target window or change its zoom afterward.
3. When the countdown ends, the program writes from the start coordinate using the previewed paths.

Press `ESC` during coordinate detection, the start countdown, or writing. During writing, quickly moving the pointer to any screen corner also triggers the failsafe. The program releases the left mouse button after completion, cancellation, or an error.

## 9. Troubleshooting

- **SmartScreen shows an unknown publisher**: the program is currently unsigned. Run only a complete folder obtained from this project.
- **Settings cannot be saved**: move the complete program folder to a writable location such as Documents or Desktop.
- **Strokes break**: increase Sample delay and avoid an unstable or overly fast target brush.
- **Curves look rough**: lower Curve detail; lower values increase writing time.
- **Output is offset**: detect the coordinates again and do not move the canvas, window, or zoom after the countdown.
- **Kaomoji proportions look wrong**: adjust character gap and verify the intended halfwidth or fullwidth symbols.
