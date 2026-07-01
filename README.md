# 日文筆順滑鼠書寫工具 V1.0

這個工具用滑鼠在小畫家或其他畫布程式中，依 KanjiVG 筆順書寫平假名、片假名與漢字。所有文字都使用逐筆中心線資料，不描繪字型外框，也不支援英數字替代模式。

第一次使用請閱讀：[圖文使用教學](圖文使用教學.md)。

## 安裝

```powershell
python -m pip install -r requirements.txt
python install_kanjivg.py
```

專案已包含 KanjiVG 資料時不必重複下載。安裝程式會把資料放在 `data/kanjivg/20250816/main/kanji`，完成後自動刪除下載壓縮檔。

## 預覽筆順

```powershell
python mouse_writer_pro.py --text "日本語かなカナ" --preview preview.png
```

預覽不會移動滑鼠。紅色數字表示每一筆的開始順序。

## 取得畫布座標

開啟小畫家並把滑鼠移到預定書寫區域，再執行：

```powershell
python locate_position.py --snapshot-after 3
```

將輸出的座標填入 `--start-x` 與 `--start-y`。

## 實際書寫

```powershell
python mouse_writer_pro.py --text "日本語かなカナ" --start-x 877 --start-y 325 --execute
```

程式倒數時切到小畫家，確認選擇的是鉛筆或筆刷，不是直線或圖形工具。Windows 版會使用 `SendInput` 並禁止系統合併曲線移動事件。執行期間若需緊急停止，快速把滑鼠移到整個螢幕左上角。

## 常用參數

- `--text "文字"`：平假名、片假名、漢字，可包含空格與換行。
- `--start-x 877 --start-y 325`：第一個字左上角的螢幕座標。
- `--char-width 150 --char-height 150`：單字書寫範圍。
- `--char-gap 12 --line-gap 24`：字距與行距。
- `--sample-spacing 2.0`：曲線取樣間距，越小越平滑但較慢。
- `--point-step 1`：滑鼠點取樣，`1` 最細緻。
- `--point-delay 0.008`：每個曲線取樣點送出後的等待時間；直線、漏畫或斷線時可提高到 `0.012`。
- `--move-duration 0.002`：額外放慢每個取樣點的移動，通常維持 `0` 即可。
- `--preview preview.png`：只輸出預覽，不移動滑鼠。
- `--execute`：實際控制滑鼠書寫。

若字元不是日文書寫字元，或本機 KanjiVG 沒有其筆順檔，程式會停止並列出該字元，不會改用字型輪廓。

## 資料來源

筆順資料來自 [KanjiVG](https://kanjivg.tagaini.net/)（[GitHub](https://github.com/KanjiVG/kanjivg)），採 Creative Commons Attribution-Share Alike 3.0 授權。
