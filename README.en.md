# Japanese Stroke Mouse Writer V2.7.0 Development

A portable Windows 10/11 x64 mouse-writing tool. It converts Japanese text, alphanumeric characters, and supported symbols into centerline strokes, then writes them in Paint or another mouse-driven canvas.

[繁體中文](README.md) / [日本語](README.ja.md)

## Installation

1. Place the complete `JapaneseStrokeMouseWriter-v2.7.0-development-win-x64-portable` folder in a writable location such as Documents or Desktop.
2. Do not move the EXE alone. Keep `_internal`, `user_data`, and all bundled files in their original relative locations.
3. Run `JapaneseStrokeMouseWriter.exe`. Python and administrator privileges are not required.
4. If Windows SmartScreen shows an unknown-publisher warning, verify that the files came from this project before choosing **More info** and **Run anyway**. The program is currently unsigned.

Settings are stored in `user_data/settings.json` inside the program folder. Registry and AppData are not used, so the folder must be writable by the current account.

## Quick Start

1. Open Paint or another target canvas and select its pen or pencil tool.
2. Enter text in **Content & Preview**.
3. Use **Detect start coordinates** and **Detect end coordinates** to define the writable rectangle.
4. Select KanjiVG, Yomogi, Zen Kurenaido, or Hachi Maru Pop and adjust font size, character gap, line gap, orientation, and flow in **General Settings**.
5. Click **Update preview** and confirm that every black writing path is inside the rectangle.
6. Click **Start writing**, then switch to the target canvas during the countdown.

Open the offline [HTML Complete Guide](complete-guide.en.html) for detailed instructions and coordinate directions. A [Markdown version](complete-guide.en.md) is also available on GitHub.

## Features

- Selects KanjiVG Original, Yomogi Direct Centreline, Zen Kurenaido Direct Centreline, or Hachi Maru Pop Direct Centreline; preview and mouse output use the same path data.
- Preserves spaces, Tab, explicit and repeated line breaks, and wraps automatically at the writable boundary.
- Supports horizontal, vertical, right, and left layouts. Preview and mouse output use the same path data.
- Halfwidth characters occupy `0.5` cell; fullwidth and wide characters occupy `1` cell. Adjacent halfwidth characters use half the character gap; other pairs use the full gap.
- Saves font size, character gap, line gap, orientation, flow, and writing style as multiple named presets.
- Provides light, dark, and Windows-following appearance modes. New users start with the light theme, and switching appearance preserves current input and session state.
- Accepts manually assembled Kaomoji such as `(^O^)`, `(≧▽≦)`, `m(_ _)m`, `(/ω＼)`, and `(╯°□°)╯︵ ┻━┻`. Each supported character is written with centerline strokes.

## Supported Text

Supported input includes Japanese kana, kanji available in KanjiVG, `A–Z`, `a–z`, `0–9`, fullwidth alphanumerics, and halfwidth katakana. Valid voiced and semi-voiced combinations such as `ｶﾞ` and `ﾊﾟ` are merged into one half-cell character.

Yomogi contains 6,608 direct-centreline SVGs, with 96 catalog fallbacks, and includes the style-only kana `ゟ` and `ヿ`. Zen Kurenaido contains 6,591 direct SVGs and 111 fallbacks. Hachi Maru Pop contains 6,608 direct SVGs and 94 fallbacks. All three direct styles prioritize the final visual result; path order is not traditional stroke order.

Printable ASCII punctuation and fullwidth counterparts are supported, including `#＃`, `(（`, `)）`, `[［`, `]］`, `@＠`, and `~～`. Japanese symbols include `、､`, `。｡`, `・･`, `ーｰ`, `「」`, `【】`, and `｢｣`.

All 128 Unicode Box Drawing characters in `U+2500–U+257F` are supported. Set character gap and line gap to `0 px` to connect adjacent cells such as `┏━┷━┓`.

The program supports some commonly used special symbols, including geometry, stars, checks, arrows, brackets, and mathematics: `☆★`, `○●`, `△▲`, `◇◆`, `□■`, and `✓✔`. Not every special symbol is available. See [Supported Centerline Symbols](SUPPORTED_SYMBOLS.md) for the complete list; unsupported characters are reported before writing starts.

## Roadmap

- Continue expanding special symbols that work well as centerline strokes.

## Emergency Stop

Press `ESC` during coordinate detection, the start countdown, or writing. During writing, quickly moving the pointer to any screen corner also triggers the failsafe. The program releases the left mouse button when stopped.

## License

Project code and project-authored centerline SVG files use the MIT License. KanjiVG data uses CC BY-SA 3.0. Yomogi, Zen Kurenaido, Hachi Maru Pop, and their derived centreline data use the SIL Open Font License 1.1. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
