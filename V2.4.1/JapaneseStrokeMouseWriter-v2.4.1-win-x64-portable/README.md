# Japanese Stroke Mouse Writer V2.4.1 Internal

Windows 10/11 x64 免安裝書寫工具。程式透過 Windows SendInput，在小畫家或其他畫布中書寫日文、英文、數字、常用符號、半形片假名，以及可用來自行拼湊顏文字的中心線符號。

[English](README.en.md) / [日本語](README.ja.md)

## 安裝方式

V2.4.1 是內部開發版，不建立 GitHub Release、不建立 tag，也不提供 ZIP。請使用 repo 內的未壓縮資料夾：

1. 開啟 `V2.4.1/JapaneseStrokeMouseWriter-v2.4.1-win-x64-portable/`。
2. 執行 `JapaneseStrokeMouseWriter.exe`。
3. 設定會寫入同資料夾旁的 `user_data/settings.json`，不使用 Registry 或 AppData。

## 功能

- KanjiVG 筆順書寫日文假名、漢字、英數字、半形片假名與常用符號。
- 半形字元占 `0.5` 格，全形／寬字元占 `1` 格；半形對半形使用半字距，其餘組合使用完整字距。
- 使用者可自行輸入或貼上顏文字，例如 `(^O^)`、`(≧▽≦)`、`m(_ _)m`、`(/ω＼)`、`¯\_(ツ)_/¯`、`(╯°□°)╯︵ ┻━┻`。
- 顏文字不再使用內建分類或依賴字型外觀，所有字元皆使用中心線筆跡逐字書寫。
- 不支援彩色 emoji、keycap emoji、ZWJ 組合與未收錄的圖像式符號。

## 支援符號

支援 `A–Z`、`a–z`、`0–9`、全形英數、半形片假名濁音如 `ｶﾞ`，以及可列印 ASCII 標點及其全形對應，例如 `#＃`、`(（`、`)）`、`[［`、`]］`、`@＠`、`~～`。日文標點包含 `、､`、`。｡`、`・･`、`ーｰ`、`「」`、`【】`、`｢｣`。

V2.4.1 另新增一組適合拼湊顏文字的中心線符號，完整清單見 [V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md](V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md)。

## 簽章狀態

SignPath Foundation 申請未核准，目前版本暫維持未簽章，且沒有正在導入的正式簽章流程。Windows SmartScreen 可能顯示未知發行者提示。

## 授權

專案程式碼與自製中心線 SVG 採 MIT License。KanjiVG 資料維持 CC BY-SA 3.0。詳見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
