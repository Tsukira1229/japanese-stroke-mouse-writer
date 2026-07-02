# Japanese Stroke Mouse Writer V2.0.1 Portable

Windows 10/11 x64 免安裝日文筆順書寫工具。程式使用 KanjiVG 筆順資料，透過 Windows SendInput 在小畫家或其他畫布中書寫平假名、片假名與漢字。

## 一般使用者

1. 下載 `JapaneseStrokeMouseWriter-v2.0.1-win-x64-portable.zip`。
2. 將 ZIP 完整解壓到可寫入的資料夾。
3. 雙擊 `JapaneseStrokeMouseWriter.exe`。

不需要安裝 Python、不需要管理員權限，也不會建立安裝或解除安裝項目。程式設定保存在同一資料夾的 `user_data/settings.json`。

## 主要功能

- 平假名、片假名與漢字皆使用 KanjiVG 筆順中心線。
- 水平／垂直排版，並可選擇向左／向右流向。
- 偵測起始座標與末端座標，形成實際可書寫矩形。
- 到達主方向邊界時自動換行，整體超出畫布時在書寫前停止。
- 完整保留空格、全形空格、Tab 與明確換行。
- 預覽與實際書寫共用相同排版資料。
- 可保存多個一般排版自訂選項。
- ESC 全域緊急停止，並保留滑鼠移到螢幕角落的 failsafe。

完整步驟請閱讀 [圖文使用教學](圖文使用教學.md)。

## 開發與測試

```powershell
python -m pip install -r requirements.txt -r requirements-build.txt
python -B -m unittest discover -s tests -v
.\scripts\build_portable.ps1
```

建置結果位於：

```text
dist/JapaneseStrokeMouseWriter-v2.0.1-win-x64-portable.zip
```

執行封裝自測：

```powershell
JapaneseStrokeMouseWriter.exe --self-test
```

## 資料來源

筆順資料來自 [KanjiVG](https://kanjivg.tagaini.net/)（[GitHub](https://github.com/KanjiVG/kanjivg)），採 Creative Commons Attribution-ShareAlike 3.0 授權。詳見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

V2.0.1 為未簽章版本，Windows SmartScreen 可能顯示未知發行者提示。
