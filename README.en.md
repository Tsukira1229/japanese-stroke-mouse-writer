# Japanese Stroke Mouse Writer V2.4.0 Portable

[繁體中文](README.md) | English | [日本語](README.ja.md)

A portable writing tool for Windows 10/11 x64. It uses Windows SendInput to write Japanese, English letters, numbers, common symbols, and newly supported kaomoji drawn from font outlines for precise text-face shapes.

## Installation

1. Download `JapaneseStrokeMouseWriter-v2.4.0-win-x64-portable.zip` from the GitHub Release.
2. Extract the entire ZIP to a writable folder.
3. Double-click `JapaneseStrokeMouseWriter.exe`.

Python and administrator privileges are not required. The program creates no installer or uninstaller entries. Settings are stored in `user_data/settings.json` beside the executable.

## Supported Content

- Japanese: hiragana, katakana, halfwidth katakana, and KanjiVG-supported kanji. Combinations such as `ｶﾞ` and `ﾊﾟ` become one half-cell glyph.
- Small kana: contracted-sound kana, small tsu, small vowels, and other included small hiragana and katakana retain their reduced size.
- English: halfwidth `A–Z`, `a–z`, plus fullwidth `Ａ–Ｚ`, `ａ–ｚ`.
- Numbers: halfwidth `0–9` plus fullwidth `０–９`.
- ASCII punctuation and fullwidth counterparts: <code>!！ "＂ #＃ $＄ %％ &＆ '＇ (（ )） *＊ +＋ ,， -－ .． /／ :： ;； &lt;＜ =＝ &gt;＞ ?？ @＠ [［ \\＼ ]］ ^＾ _＿ `｀ {｛ |｜ }｝ ~～</code>.
- Japanese punctuation and brackets: `、､ 。｡ ・･ ーｰ 「」 『』 【】 〈〉 《》 〔〕 ｢｣`.
- Kaomoji: built-in categories for happy, cute, greeting/apology, shy, love, sad/crying, angry, surprised, anxious/sweat, sleepy/tired, shrug, action/gesture, and animal/character faces.
- Kaomoji are drawn from font outlines, so black preview paths match mouse output. Each kaomoji is handled as one run and is never auto-wrapped in the middle.
- Unicode halfwidth/narrow characters occupy `0.5` cell; fullwidth/wide characters occupy `1` cell. Paired forms share stroke data.
- A normal space occupies `0.5` cell, a fullwidth space occupies `1` cell, and Tab displays four half-cells occupying `2` cells. Line breaks are preserved.
- Adjacent halfwidth characters use half the configured character gap. A pair containing any fullwidth character uses the full gap. Spaces and Tab follow the same rule.

Unsupported characters, missing stroke data, color emoji, keycap sequences, and ZWJ sequences are rejected before the mouse moves.

## Main Features

- Horizontal or vertical layout with left or right flow.
- Vertical layout automatically rotates letters, numbers, brackets, and long marks, and moves `、。` to the upper-right corner.
- Start/end coordinate detection, automatic wrapping, and bounds checking.
- Preview and mouse output share the same layout paths.
- The Content & Preview page can insert curated kaomoji by category.
- Multiple named layout presets.
- Japanese, Traditional Chinese, Simplified Chinese, and English desktop UI.
- Global ESC emergency stop and screen-corner failsafe.
- Maximized startup, an emergency-stop hint in the bottom status bar, and an in-app Help tab.

See the [complete guide](complete-guide.en.md) for operating instructions.

## Data Sources

Japanese, English, number, and selected symbol stroke data comes from [KanjiVG](https://kanjivg.tagaini.net/) ([GitHub](https://github.com/KanjiVG/kanjivg)) under CC BY-SA 3.0. Missing ASCII symbols, Japanese brackets, `～`, and `@` use project-authored centerline paths. Kaomoji categories follow common kaomoji classification patterns, and the built-in list is curated by this project. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License and Code signing policy

Project code and project-authored stroke data use the [MIT License](LICENSE). See the [Code signing policy](CODE_SIGNING_POLICY.md), [privacy statement](PRIVACY.md), and [security policy](SECURITY.md).

The project applied for SignPath Foundation open-source code signing but was not approved at this time. V2.4.0 remains unsigned, so Windows SmartScreen may display an unknown-publisher warning.
