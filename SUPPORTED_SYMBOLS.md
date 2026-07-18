# Supported Centerline Symbols

V2.7.0 supports these centerline symbols for users who want to assemble kaomoji and line drawings manually.

Total additional centerline symbols: 430

This list is generated from `data/symbol_manifest.json`; edit the manifest and run `python scripts/manage_symbol_catalog.py generate-docs`.
For the complete addition and review procedure, see [Special-symbol development workflow](SYMBOL_DEVELOPMENT.md).

## Accent / small mark

¨ ¯ ° ´ · º ˊ ˋ ˘ ˙ ⁄

## Arms / hands

ʔ ʕ و ٩ ۶ ୧ ୨ ฅ ง ༼ ༽ ლ ᐕ ᐖ ᐛ ᐟ ᐠ ᐡ ᐢ ᕕ ᕗ ᕙ ᕤ ᕦ ᘚ ᘛ ∪ ⊂ ⊃ ꒰ ꒱

## Emoticon symbol

ღ ᗜ ᵇ ᵈ ᵗ •

## Eyes

ʘ ˂ ˃ ಠ ≖ ◉ ◎ ◔ ◕ ☉ ꇴ ꒪

## Eyes, Math / relation

⊙

## Lines / objects

¬ ⊥ ︵

## Love / sparkle

๑ ᴗ ◡ ☼ ☾ ♡ ♥ ✦ ✧ ✩ ✪ ✿ ❁ ❛

## Math / relation

∑ ≦ ≧ ≠ ≡ ≈ ≋ ≌ ≺ ≻ ≪ ≫ ∝ ∠ ∴ ∵ ∷ ∼ ∽ ∣ ∥ ∧ ∨ ∩ ⊆ ⊇ ⊊ ⊋ ⊄ ⊅

## Mouth / face part

˶ ε ω Д д з ᆺ ᴥ ᵒ ᵔ ᵕ ᵘ ‿ ∀ ∇ □ ▽ ㅁ ㅂ ㅅ ㅇ ㅈ ㅎ ㅜ ㅠ ︶ ︿ ﹏ ﻌ

## Tears / stress

꒦ ꒨ ಥ ಢ ಡ ༎ །

## Brackets / curves

⌒ ⌣ ⌢ ⌜ ⌝ ⌞ ⌟ 〈 〉 ⟨ ⟩ ⟪ ⟫ ⟦ ⟧ ⟮ ⟯ ⸜ ⸝ ⸨ ⸩ ⸢ ⸣ ⸤ ⸥

## Eyes / face geometry

◌ ◍ ◐ ◑ ◒ ◓ ◖ ◗ ◘ ◙ ◚ ◛ ◜ ◝ ◞ ◟ ◠ ◇

## Arms / pose

ʚ ɞ ᓄ ᓂ ᓀ ᓁ ᓆ ᓇ ᓈ ᓉ ᗒ ᗕ ᗣ ᗨ ᗩ ᗪ

## Sparkle / decoration

⋆ ⋄ ✣ ✤ ✥ ✫ ✬ ✭ ✮ ✯

## Unicode Box Drawing (U+2500-U+257F)

All 128 Unicode Box Drawing characters are supported with direct code-point SVG resources. Light lines use one stroke, heavy lines use three close parallel strokes, and double lines use two separated strokes. Set character gap and line gap to `0 px` when adjacent cells must connect.

```text
─━│┃┄┅┆┇┈┉┊┋┌┍┎┏
┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟
┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯
┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿
╀╁╂╃╄╅╆╇╈╉╊╋╌╍╎╏
═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟
╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯
╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿
```

## Common Unicode symbol variants

Each of these 89 characters has its own direct code-point SVG. Filled geometric shapes use an outer boundary plus sparse diagonal hatching. Brackets rotate in vertical layout; arrows preserve their semantic direction.

```text
±×÷⁅⁆←↑→↓↔↕↖↗↘↙⇐
⇑⇒⇓⇔⇕∂∅∆∈∉∋∏√∞∫≤
≥⊕⊗■▪▫▲△▴▵▶▷▸▹▼▾
▿◀◁◂◃◆◈○●◦◯◻◼◽◾★
☆♢♦⚝✓✔✕✖✗✘❨❩❪❫❬❭
❰❱❲❳❴❵⭐⭑⭒
```

## Representative supported kaomoji

```text
(^O^)
(≧▽≦)
m(_ _)m
(/ω\)
¯\_(ツ)_/¯
(╯°□°)╯︵ ┻━┻
ฅ^•ﻌ•^ฅ
(˶ᵔ ᵕ ᵔ˶)
ლ(ಠ益ಠ)ლ
ʕ•ᴥ•ʔ
ᕕ(ᐛ)ᕗ
(ㅠ﹏ㅠ)
ʚ(˶◜ᵕ◝˶)ɞ
⸜(｡˃ ᵕ ˂ )⸝
```

These symbols are written as normal characters. They do not create a single protected kaomoji run, and they do not use font-dependent drawing. Combining marks, emoji, keycap sequences, ZWJ sequences, and unsupported pictorial symbols are rejected before mouse movement.
