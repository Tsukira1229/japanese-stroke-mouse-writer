# 日文筆順滑鼠書寫工具 V1.0

這個 Windows 工具會依照 KanjiVG 筆順，用滑鼠在小畫家或其他畫布程式中書寫平假名、片假名與漢字。一般使用者可在圖形介面中輸入文字、調整位置與尺寸、預覽筆順並開始書寫，不必操作程式碼或命令列參數。

## 第一次安裝

1. 安裝 [Python 3](https://www.python.org/downloads/windows/)，安裝時勾選 **Add Python to PATH**。
2. 在本資料夾開啟終端機。
3. 執行：

```powershell
python -m pip install -r requirements.txt
```

專案已包含 KanjiVG 筆順資料，不需要另外下載。

## 開啟工具

雙擊 `run_writer.bat`，即可開啟「日文筆順書寫工具」視窗。

## 基本操作

1. 在「書寫文字」輸入平假名、片假名或漢字。
2. 按「擷取滑鼠位置」，在 3 秒內把滑鼠移到畫布的書寫起點。
3. 調整字寬、字高、字距或速度。
4. 按「產生預覽」確認筆順。
5. 開啟小畫家並選擇鉛筆或筆刷。
6. 按「開始書寫」，視窗會自動最小化並倒數。

執行期間若需緊急停止，將滑鼠快速移到螢幕左上角。

## 檔案用途

- `run_writer.bat`：一般使用者的 UI 啟動器。
- `mouse_writer_ui.pyw`：圖形操作介面。
- `mouse_writer_pro.py`：筆順解析與滑鼠書寫核心，也可供進階命令列操作。
- `data/kanjivg`：平假名、片假名與漢字筆順資料。
- `install_kanjivg.py`：需要重新下載筆順資料時使用。

完整操作與問題排除請閱讀 [圖文使用教學](圖文使用教學.md)。

## 資料來源

筆順資料來自 [KanjiVG](https://kanjivg.tagaini.net/)（[GitHub](https://github.com/KanjiVG/kanjivg)），採 Creative Commons Attribution-Share Alike 3.0 授權。
