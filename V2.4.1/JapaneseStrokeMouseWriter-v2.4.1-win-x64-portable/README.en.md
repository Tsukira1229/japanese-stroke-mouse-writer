# Japanese Stroke Mouse Writer V2.4.1 Internal

A portable Windows 10/11 x64 writing tool. It uses Windows SendInput to write Japanese, English letters, numbers, common symbols, halfwidth katakana, and centerline symbols that users can combine into kaomoji.

[繁體中文](README.md) / [日本語](README.ja.md)

## Installation

V2.4.1 is an internal development build. It does not create a GitHub Release, tag, or ZIP. Use the uncompressed folder in this repository:

1. Open `V2.4.1/JapaneseStrokeMouseWriter-v2.4.1-win-x64-portable/`.
2. Run `JapaneseStrokeMouseWriter.exe`.
3. Settings are written to `user_data/settings.json` beside the executable folder. Registry and AppData are not used.

## Features

- Writes Japanese kana, kanji, English letters, numbers, halfwidth katakana, and common symbols using KanjiVG or project-authored centerline strokes.
- Halfwidth characters occupy `0.5` cell; fullwidth and wide characters occupy `1` cell. Adjacent halfwidth characters use half the character gap; all other pairs use the full gap.
- Users can type or paste kaomoji manually, such as `(^O^)`, `(≧▽≦)`, `m(_ _)m`, `(/ω＼)`, `¯\_(ツ)_/¯`, and `(╯°□°)╯︵ ┻━┻`.
- Kaomoji no longer use built-in categories or font-dependent drawing. Every character is written one by one with centerline strokes.
- Color emoji, keycap emoji, ZWJ sequences, and unsupported pictorial symbols are rejected before the mouse moves.

## Supported Symbols

Supported input includes `A–Z`, `a–z`, `0–9`, fullwidth alphanumerics, halfwidth katakana voiced pairs such as `ｶﾞ`, printable ASCII punctuation and fullwidth counterparts such as `#＃`, `(（`, `)）`, `[［`, `]］`, `@＠`, and `~～`. Japanese punctuation includes `、､`, `。｡`, `・･`, `ーｰ`, `「」`, `【】`, and `｢｣`.

V2.4.1 also adds centerline symbols useful for assembling kaomoji. See [V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md](V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md).

## Code Signing

The SignPath Foundation application was not approved. Current builds remain unsigned, and there is no active official signing integration. Windows SmartScreen may show an unknown-publisher warning.

## License

Project code and project-authored centerline SVG files are MIT licensed. KanjiVG data remains CC BY-SA 3.0. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
