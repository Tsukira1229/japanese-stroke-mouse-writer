# 特殊符號 SVG 擴充交接報告

- 交接日期：2026-07-20
- 工作目錄：`C:\Users\User\.codex\DATA\滑鼠繪字工具`
- 目前分支：`main`
- 基準提交：`2d64a05`（`v2.7.1`，與 `origin/main` 一致）
- 工作樹：單一 worktree；本次內容尚未建立分支、尚未暫存、尚未提交

## 1. 交接結論

本輪特殊符號工作已完成五個批次的 SVG 製作、固定字格疊圖審查及使用者驗收。第五批 `kaomoji-bracket-ornament-05` 已由 `in_progress` 更新為 `verified`；目前 manifest 與候選表均無待審項目。

- Manifest 支援數：430 → 514，淨增加 84 個 Unicode 符號。
- 分組數量：`box_drawing` 128、`common_variant` 108、`emoticon` 278，合計 514。
- `data/custom_strokes/` 現有 554 個 SVG。
- 相對於基準提交共有 86 個未追蹤 SVG：84 個新符號資源，加上 `!／！` 與 `?／？` 共用的 2 個自製輪廓資源。
- 本輪未執行實際滑鼠書寫、未建立 portable、未封裝。
- 依工作邊界，本輪未修改 Python 程式或測試；工作樹中現有的輸入診斷程式變更屬另一工作流。

## 2. 已驗收批次

| 批次 | 數量 | 符號 | 審查證據 |
|---|---:|---|---|
| `kaomoji-eyes-geometry-01` | 15 | ◴ ◵ ◶ ◷ ⊖ ⊘ ⊚ ⊛ ⊜ ⊝ ⊞ ⊟ ⊠ ⊡ ⦿ | [總覽](build/symbol-review/kaomoji-eyes-geometry-01/overview.png)／[清單](build/symbol-review/kaomoji-eyes-geometry-01/checklist.md) |
| `kaomoji-sparkle-decoration-02` | 16 | ✢ ✱ ✲ ✳ ✴ ✵ ✶ ✷ ✸ ✹ ✺ ✻ ✼ ✽ ✾ ❀ | [總覽](build/symbol-review/kaomoji-sparkle-decoration-02/overview.png)／[清單](build/symbol-review/kaomoji-sparkle-decoration-02/checklist.md) |
| `kaomoji-dingbat-decoration-03` | 17 | ❂ ❃ ❄ ❅ ❆ ❇ ❈ ❉ ❊ ❋ ❌ ❍ ❎ ❏ ❐ ❑ ❒ | [總覽](build/symbol-review/kaomoji-dingbat-decoration-03/overview.png)／[清單](build/symbol-review/kaomoji-dingbat-decoration-03/checklist.md) |
| `kaomoji-dingbat-punctuation-heart-04` | 18 | ❓ ❔ ❕ ❖ ❗ ❘ ❙ ❚ ❜ ❝ ❞ ❟ ❠ ❡ ❢ ❣ ❤ ❥ | [總覽](build/symbol-review/kaomoji-dingbat-punctuation-heart-04/overview.png)／[清單](build/symbol-review/kaomoji-dingbat-punctuation-heart-04/checklist.md) |
| `kaomoji-bracket-ornament-05` | 18 | ❮ ❯ ⦃ ⦄ ⦅ ⦆ ⦇ ⦈ ⦉ ⦊ ⦋ ⦌ ⦍ ⦎ ⦏ ⦐ ⦑ ⦒ | [總覽](build/symbol-review/kaomoji-bracket-ornament-05/overview.png)／[清單](build/symbol-review/kaomoji-bracket-ornament-05/checklist.md) |

上述 `build/symbol-review/` 審查產物受 `.gitignore` 的 `build/` 規則排除，屬本機驗收證據，不會隨一般提交進入版本控制。如需長期保存，版本控制小組應另行決定歸檔位置，不要直接解除整個 `build/` 的忽略規則。

## 3. 重要造形決策

- `!／！` 使用 `data/custom_strokes/00021.svg`；`?／？` 使用 `data/custom_strokes/0003f.svg`。主體與圓點均採外輪廓，圓點為獨立 path。
- `❓ ❔ ❕ ❗ ❙ ❚` 採主體外輪廓；帶圓點者的圓點為獨立輪廓，不與主體連線。
- `❦` U+2766、`❧` U+2767 依使用者決定不加入；manifest、候選表及 SVG 均不存在這兩項。
- 實心裝飾符號採可辨識的外輪廓、中心骨架或稀疏結構，不使用密集填色筆畫。
- 每個分離部件各自使用 `<path>`，避免滑鼠書寫時產生跨部件連線。
- 所有資源維持 `viewBox="0 0 109 109"`，半格字元由 manifest 的 `cell_span` 與排版層縮放；第五批 `⦅ ⦆` 已校正為 `0.5`。

## 4. 建議納入特殊符號提交的檔案

### 追蹤中檔案

- `SUPPORTED_SYMBOLS.md`
- `data/symbol_manifest.json`
- `data/symbol_candidates.csv`
- `SYMBOL_SVG_HANDOFF_2026-07-20.md`

### 新增 SVG

共 86 個未追蹤檔案，全部位於 `data/custom_strokes/`：

- 核心標點輪廓：`00021.svg`、`0003f.svg`
- 第一批：U+25F4–U+25F7、U+2296、U+2298、U+229A–U+22A1、U+29BF
- 第二批：U+2722、U+2731–U+273E、U+2740
- 第三批：U+2742–U+2752
- 第四批：U+2753–U+275A、U+275C–U+2765
- 第五批：U+276E–U+276F、U+2983–U+2992

提交前應先確認下列盤點仍回傳 `86`，再暫存列出的 SVG，避免使用未審查的廣泛 `git add .`：

```powershell
$newSvg = @(git ls-files --others --exclude-standard -- data/custom_strokes/*.svg)
if ($newSvg.Count -ne 86) { throw "Expected 86 new SVGs, got $($newSvg.Count)" }
$newSvg | ForEach-Object { git add -- $_ }
git add -- SUPPORTED_SYMBOLS.md data/symbol_manifest.json data/symbol_candidates.csv SYMBOL_SVG_HANDOFF_2026-07-20.md
```

## 5. 不可混入本次符號提交的工作樹內容

下列檔案屬「跨筆畫輸入診斷／小畫家相容模式」工作流，與本次 SVG 擴充無關，應由其負責人另行審查及提交：

- `localization.py`
- `mouse_writer_pro.py`
- `mouse_writer_ui.pyw`
- `input_diagnostics.py`
- `tests/test_input_diagnostics.py`
- `INPUT_DIAGNOSTICS_TESTING.ja.txt`

除非版本控制小組有意合併兩個功能，否則不要暫存上述檔案。

## 6. 驗證結果

| 驗證 | 結果 |
|---|---|
| `python scripts/manage_symbol_catalog.py validate` | 通過；514 個符號 |
| 全 manifest `build_layout` | 通過；514 個符號 × 4 種排列，共 2,056 模式；路徑非空、筆畫數相符且位於字格內 |
| 第五批比較卡 | 18 張卡、18 項清單、1 張總覽，全部生成成功 |
| `python -m unittest tests.test_core tests.test_box_drawing` | 51/51 通過 |
| `python -m unittest discover -s tests` | 共 148 項；146 通過，2 項因舊固定數量斷言失敗，詳見下一節 |
| `git diff --check` | 通過；僅顯示 Git 的 LF/CRLF 提示，沒有空白錯誤 |
| 實際滑鼠輸出 | 未執行 |
| Portable／封裝／雜湊同步 | 依工作邊界未執行 |

## 7. 版本控制小組需處理的兩個舊數量斷言

目前完整測試的兩個失敗均為擴充後未更新的固定數字，不是 SVG 解析或排版失敗：

1. `tests/test_common_symbol_variants.py:36`
   - 現況：斷言 `len(EXPECTED) == 89`
   - 實際：108
   - 建議：改為由 manifest／分組資料推導，或至少同步為 108。
2. `tests/test_symbol_catalog.py:54`
   - 現況：斷言 manifest 總數為 430
   - 實際：514
   - 建議：改為可維護的 manifest 一致性檢查，避免下批擴充再次手動修改固定數量。

另有一處文件產生器的固定敘述：

- `scripts/manage_symbol_catalog.py:87` 仍輸出「Each of these 89 characters...」，因此剛生成的 `SUPPORTED_SYMBOLS.md` 雖然總數與符號內容正確，該句仍是舊數字。
- 依本輪「不改程式」邊界未處理。版本控制小組應將敘述改為依 `common_variant` 實際數量動態生成，重新執行 `python scripts/manage_symbol_catalog.py generate-docs`，再跑完整測試。

## 8. 交接時的檔案雜湊

- `data/symbol_manifest.json`：`D07E2384C68DCC49CACA459A73D1E9A3D01A55E7D07103831276485E9E9F9E78`
- `data/symbol_candidates.csv`：`E55E79374E1179E962634C22037543D3E59C8F2669F95CAE914952BB9D5F4D90`
- `SUPPORTED_SYMBOLS.md`：`8EE062BD7821B34438F8C86F408F15B0099649C8B90E4CC6B3F0255644A8A0ED`

若版本控制小組修正文件產生器並重新生成 `SUPPORTED_SYMBOLS.md`，第三個雜湊預期會改變；前兩個來源資料不應因純文件修正而變動。

## 9. 建議提交完成條件

1. 將特殊符號檔案與輸入診斷工作分開暫存。
2. 修正三處舊數量來源：兩個測試斷言及一個產生器敘述。
3. 重新生成 `SUPPORTED_SYMBOLS.md`。
4. 再執行 catalog 驗證、2,056 模式 layout 驗證、完整 148 項單元測試及 `git diff --check`。
5. 版本發布階段才執行 portable 建置與來源／封裝 SVG 雜湊同步；本次資產審查階段未授權封裝。
6. 建議提交訊息：`feat(symbols): add 84 reviewed Unicode centerline symbols`

## 10. 版本控制整合結果

- 暫定版本：V2.7.2 內部開發版。
- 整合分支：`codex/internal-v2.7.2-symbols`。
- 已移除兩個測試與文件產生器的固定舊數量；支援文件已由 514 筆 manifest 重新產生。
- 完整工作樹測試：148/148 通過；其中包含另一工作流尚未提交的4項輸入診斷測試。
- 符號提交暫存快照測試：144/144通過，V2.7.2原始碼自我測試通過；514個符號與2,056種排列組合驗證通過。
- `localization.py`、`mouse_writer_ui.pyw`、輸入診斷模組及其測試維持未暫存，不納入本次符號整合。
- 本版不建立 Portable、不建立 tag、不建立 GitHub Release。
