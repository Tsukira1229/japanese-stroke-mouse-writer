# Japanese Stroke Mouse Writer V2.1.1 Portable

繁體中文 | [English](README.en.md) | [日本語](README.ja.md)

Windows 10/11 x64 免安裝筆順書寫工具。程式透過 Windows SendInput，在小畫家或其他畫布中依中心線筆順書寫日文、英文、數字與常用符號。

## 安裝方式

1. 下載 `JapaneseStrokeMouseWriter-v2.1.1-win-x64-portable.zip`。
2. 將 ZIP 完整解壓到可寫入的資料夾。
3. 雙擊 `JapaneseStrokeMouseWriter.exe`。

不需要安裝 Python、不需要管理員權限，也不會建立安裝或解除安裝項目。設定保存在程式旁的 `user_data/settings.json`。

## 支援內容

- 日文：平假名、片假名及 KanjiVG 收錄的漢字。
- 英文：`A–Z`、`a–z`。
- 數字：`0–9`。
- 符號：`, . ! ? : ; 、。・ー ，～@`。
- 符號會保留自然尺寸與字格內位置，例如逗號、句點、頓號位於字格下方。
- 一般空格、全形空格、Tab 與換行會完整保留。

未列入支援範圍或缺少筆順資料的字元，會在移動滑鼠前停止並顯示錯誤。

## 主要功能

- 水平／垂直排版，以及向左／向右流向。
- 起始與末端座標偵測、自動換行及超界預防。
- 預覽與實際書寫共用相同排版路徑。
- 多個具名排版自訂選項。
- 日文、繁體中文、簡體中文、英文桌面介面。
- ESC 全域緊急停止與螢幕角落 failsafe。

操作方式請閱讀 [完整步驟](complete-guide.md)。

## 資料來源

日文、英文、數字及部分符號筆順來自 [KanjiVG](https://kanjivg.tagaini.net/)（[GitHub](https://github.com/KanjiVG/kanjivg)），採 Creative Commons Attribution-ShareAlike 3.0。`～` 與 `@` 使用本專案建立的中心線資料。詳見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

V2.1.1 為未簽章版本，Windows SmartScreen 可能顯示未知發行者提示。
