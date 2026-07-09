# Japanese Stroke Mouse Writer V2.4.1 Complete Guide

## 1. Enter Text

Enter or paste the content in Content & Preview. Spaces, Tab, explicit line breaks, repeated line breaks, and automatic wrapping are preserved. Type kaomoji directly in the text box, for example `(^O^)`, `(≧▽≦)`, `m(_ _)m`, `(/ω＼)`, `¯\_(ツ)_/¯`, and `(╯°□°)╯︵ ┻━┻`.

V2.4.1 does not provide a kaomoji category picker and does not use font-dependent drawing. Kaomoji are written as individual centerline characters, so users can assemble their own shapes from supported symbols.

## 2. Set Coordinates

Start and end coordinates form the writable rectangle. For right flow, Start is the top-left corner and End is the bottom-right corner. For left flow, Start is the top-right corner and End is the bottom-left corner. You can enter X/Y manually or use the detection buttons. During detection the main window is minimized, and the pointer position is captured when the countdown ends. Press ESC to cancel.

## 3. Adjust Layout

Supported input includes `A–Z`, `a–z`, `0–9`, fullwidth alphanumerics, halfwidth katakana voiced pairs such as `ｶﾞ`, and common halfwidth/fullwidth symbol pairs: `#＃`, `(（`, `)）`, `[［`, `]］`, `@＠`, `~～`, `、､`, `。｡`, `・･`, `ーｰ`, `「」`, `【】`, and `｢｣`.

Font size is measured in px. Halfwidth characters occupy `0.5` cell, fullwidth and wide characters occupy `1` cell, and Tab equals four halfwidth spaces. Halfwidth katakana voiced pairs such as `ｶﾞ` are merged into one half-cell character. Halfwidth-to-halfwidth pairs use half the character gap; fullwidth pairs and mixed pairs use the full gap. Horizontal text wraps downward at the side boundary. Vertical text creates a new left or right column at the bottom boundary.

In vertical layout, letters, numbers, brackets, and long marks rotate clockwise, while `、。` move to the upper-right corner. Every character inside a kaomoji follows the normal character layout rules.

## 4. Update Preview

Click Update preview. Light cells show occupied space, and black lines are the exact mouse writing paths. Unsupported characters are reported before the mouse moves.

## 5. Start and Stop Writing

After checking the preview, click Start writing. During the countdown, switch to Paint or another target canvas and keep its pen or pencil tool selected. Press ESC during writing to stop, or move the pointer to a screen corner to trigger the failsafe. The program releases the left mouse button after stops or errors.

## 6. Troubleshooting

- **Unsupported writing character**: use characters listed in the README or `V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md`.
- **Emoji sequences are unsupported**: color emoji, keycap emoji, and ZWJ sequences are rejected before mouse movement.
- **Kaomoji shape differs from expectation**: V2.4.1 writes character-by-character centerlines; adjust symbol choices, spacing, or halfwidth/fullwidth variants.
- **SmartScreen warning**: V2.4.1 is an unsigned internal build and may show an unknown-publisher warning.
