# Japanese Stroke Mouse Writer V2.3.2 Portable

繁體中文 | [English](README.en.md) | [日本語](README.ja.md)

Windows 10/11 x64 免安裝筆順書寫工具。程式透過 Windows SendInput，在小畫家或其他畫布中依中心線筆順書寫日文、英文、數字與常用符號。

## 安裝方式

1. 下載 `JapaneseStrokeMouseWriter-v2.3.2-win-x64-portable.zip`。
2. 將 ZIP 完整解壓到可寫入的資料夾。
3. 雙擊 `JapaneseStrokeMouseWriter.exe`。

不需要安裝 Python、不需要管理員權限，也不會建立安裝或解除安裝項目。設定保存在程式旁的 `user_data/settings.json`。

## 支援內容

- 日文：平假名、片假名、半形片假名及 KanjiVG 收錄的漢字；`ｶﾞ`、`ﾊﾟ` 等組合會合併為單一半格字形。
- 小假名：拗音、促音、小母音及其他內附的小平假名／片假名會保留小字比例。
- 英文：半形 `A–Z`、`a–z`，以及全形 `Ａ–Ｚ`、`ａ–ｚ`。
- 數字：半形 `0–9`，以及全形 `０–９`。
- ASCII 符號及全形對應：<code>!！ "＂ #＃ $＄ %％ &＆ '＇ (（ )） *＊ +＋ ,， -－ .． /／ :： ;； &lt;＜ =＝ &gt;＞ ?？ @＠ [［ \\＼ ]］ ^＾ _＿ `｀ {｛ |｜ }｝ ~～</code>。
- 日文標點與括號：`、､ 。｡ ・･ ーｰ 「」 『』 【】 〈〉 《》 〔〕 ｢｣`。
- Unicode 半形／窄字元占 `0.5` 格，全形／寬字元占 `1` 格；半形與全形對應共用相同筆順。
- 一般空格占 `0.5` 格、全形空格占 `1` 格、Tab 顯示四個半格並占 `2` 格；換行會完整保留。
- 相鄰半形字元使用設定字距的一半；只要任一側為全形字元，就使用完整字距。空格與 Tab 亦使用相同規則。

未列入支援範圍或缺少筆順資料的字元，會在移動滑鼠前停止並顯示錯誤。

## 主要功能

- 水平／垂直排版，以及向左／向右流向。
- 垂直排版會自動旋轉英數、括號與長線，並將 `、。` 移至字格右上。
- 起始與末端座標偵測、自動換行及超界預防。
- 預覽與實際書寫共用相同排版路徑。
- 多個具名排版自訂選項。
- 日文、繁體中文、簡體中文、英文桌面介面。
- ESC 全域緊急停止與螢幕角落 failsafe。
- 啟動時自動最大化，緊急停止提示顯示於底部狀態列，並提供內建「使用說明」頁籤。

操作方式請閱讀 [完整步驟](complete-guide.md)。

## 資料來源

日文、英文、數字及部分符號筆順來自 [KanjiVG](https://kanjivg.tagaini.net/)（[GitHub](https://github.com/KanjiVG/kanjivg)），採 Creative Commons Attribution-ShareAlike 3.0。缺少的 ASCII 符號、日文括號、`～` 與 `@` 使用本專案建立的中心線資料。詳見 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 授權與 Code signing policy

專案程式碼與自製筆順資料採 [MIT License](LICENSE)。另請參閱 [Code signing policy](CODE_SIGNING_POLICY.md)、[隱私聲明](PRIVACY.md)及[安全政策](SECURITY.md)。目前正在申請 SignPath Foundation 開源簽章服務。

V2.3.2 為未簽章版本，Windows SmartScreen 可能顯示未知發行者提示。
