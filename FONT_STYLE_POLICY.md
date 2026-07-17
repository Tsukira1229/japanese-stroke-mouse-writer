# 筆跡風格包合格原則與首批紀錄

## 合格原則

候選字型必須同時符合下列條件，才可加入可攜版：

1. 字型檔及其衍生字型資料明確採 SIL Open Font License 1.1，允許商業使用、修改、轉換與再散布。
2. 來源必須保留完整原始著作權與 OFL 原文；若 OFL 宣告 Reserved Font Name，衍生包不得使用受保留名稱。首批三套來源的 OFL 均未宣告 Reserved Font Name。
3. 必須能固定到公開來源的特定 commit、檔案版本與 SHA-256，避免日後同名檔案漂移。
4. 字元覆蓋需與程式現有 KanjiVG／自製筆跡有足夠交集；無字形或無法產生有效骨架時必須安全退回原始筆跡。
5. 轉換後只能包含由該 OFL 字型輪廓生成的中線骨架，不得把 KanjiVG 幾何寫入 OFL 風格包。
6. 執行時投影必須保留基礎資料的筆數、筆序與筆向；投影信心不足時不得強行輸出變形筆畫。
7. 必須通過固定字格代表性樣本、橫排、直排、資源格式、manifest、授權及可攜版一致性測試；若未完成逐字人工校對，必須在 manifest 記錄校對狀態，並在程式內使用說明及完整指南揭露限制。

## 首批合格組合

| 風格包 | 原始版本 | 固定 commit | 來源字型 SHA-256 | 產生／退回 |
| --- | --- | --- | --- | --- |
| Zen Kurenaido Regular | Version 1.001 | `2edac135aa83e34640ec569d1d27520c3400e9b7` | `58b8d930d9fc10c8a5810c085bae378dacb98d0779073ee6d53d919f19ee6a4f` | 6591／111 |
| Hachi Maru Pop Regular | Version 1.300 | `252adbcc5e3722bd514c424c4a4395127f18d73c` | `78408910c8f1a2f174a279cbc1484b48b71780039eba3fe1be2bfcc5d4df3f98` | 6609／93 |
| Yomogi Regular | Version 3.100 | `2dcc1a21e9ee7cb66606d0be9099752504efe559` | `3424e34bb951e89bf5dd2554a65d8964335ea3c0560f8d1ea9aa3591ef73cba9` | 6606／96 |

每個 `data/stroke_styles/<style-id>/` 皆包含：

- `manifest.json`：機器可讀的來源 repository、commit、來源與衍生檔 SHA-256、字型版本、著作權、轉換／提升紀錄、校對狀態及統計。
- `OFL.txt`：來源專案提供的完整 OFL 與原始著作權。
- `SOURCE.md`：人類可讀的來源及轉換紀錄。
- `strokes.zip`：排序且固定 ZIP metadata 的 OFL 中線骨架，便於重建雜湊及可攜版隨機讀取。

## 授權分層

風格包是 OFL 字型輪廓的衍生資料，維持 OFL 1.1。KanjiVG 筆順資料仍為獨立的 CC BY-SA 3.0 資源；程式只在使用者預覽或書寫時暫時把它投影到所選骨架，不把合成後的幾何重新散布成風格包。專案自製筆跡仍採 MIT License。

這種中線化必然是原外框字型的近似，不應宣稱為原字型的完整外觀。缺字或低信心結果會回退，並不代表來源字型缺少商業使用權。

## 校對狀態與使用限制

Zen Kurenaido、Hachi Maru Pop、Yomogi 的正式包採用完整候選原始 SVG，不納入16個由人工圖片重建、成效不佳的 R1 試驗覆寫。共同的6,702字目錄中已有821字沿用先前人工通過幾何，另有42個關鍵字元通過本輪人工確認；其餘字元依自動品質規則產生，尚未逐字人工確認。1,300字優先清單仍有1,258字待確認，其中165字路徑異常組已擱置。

正式收錄不代表可作為標準字形、書法或筆順教材。程式以 KanjiVG／自製基礎筆跡控制筆數、筆序與筆向，再投影至字型中心線；使用者必須先查看預覽。完整使用須知只放在程式內「使用說明」及三語 `complete-guide`。

## 未納入範例

「みそら明朝」雖允許作品商用，但其散布條款不允許修改或再散布字型，且並非 OFL；因此不符合本專案風格包的必要條件，也未納入 V2.7.0。

## 重建與審查

```powershell
python -m pip install -r requirements.txt -r requirements-build.txt
python scripts/promote_full_three_font_style_packs.py --output-dir data/stroke_styles
python scripts/review_font_style_packs.py --candidate-dir data/stroke_styles
python -m unittest tests.test_stroke_styles -v
```

V2.7.0 的正式產物只納入通過上述授權、來源固定、完整性與回退驗證的三個 OFL 筆跡風格包。
