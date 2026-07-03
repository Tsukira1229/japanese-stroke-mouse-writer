# Japanese Stroke Mouse Writer V2.1.0 Portable

[繁體中文](README.md) | [English](README.en.md) | 日本語

Windows 10/11 x64 向けのインストール不要な筆順書き込みツールです。Windows SendInput を使用し、ペイントなどのキャンバスへ日本語、英字、数字、記号を中心線の筆順に沿って書き込みます。

## インストール方法

1. `JapaneseStrokeMouseWriter-v2.1.0-win-x64-portable.zip` をダウンロードします。
2. ZIP 全体を書き込み可能なフォルダーへ展開します。
3. `JapaneseStrokeMouseWriter.exe` をダブルクリックします。

Python や管理者権限は不要です。インストーラーやアンインストール項目は作成されません。設定は実行ファイル横の `user_data/settings.json` に保存されます。

## 対応文字

- 日本語：ひらがな、カタカナ、KanjiVG に収録された漢字。
- 英字：`A–Z`、`a–z`。
- 数字：`0–9`。
- 記号：`, . ! ? : ; 、。・ー ，～@`。
- 半角・全角スペース、Tab、改行はそのまま保持されます。

非対応文字や筆順データがない文字は、マウスを動かす前にエラーになります。

## 主な機能

- 横書き／縦書き、左方向／右方向の配置。
- 開始・終了座標の検出、自動折り返し、範囲チェック。
- プレビューとマウス出力で同じレイアウト経路を使用。
- 複数の名前付きレイアウトプリセット。
- 日本語、繁体字中国語、簡体字中国語、英語の画面表示。
- ESC による緊急停止と画面隅のフェイルセーフ。

操作方法は [完全ガイド](complete-guide.ja.md) を参照してください。

## データ提供元

日本語、英字、数字、一部記号の筆順データは CC BY-SA 3.0 の [KanjiVG](https://kanjivg.tagaini.net/)（[GitHub](https://github.com/KanjiVG/kanjivg)）を使用しています。`～` と `@` の中心線は本プロジェクトで作成しました。詳細は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。

V2.1.0 は未署名のため、Windows SmartScreen に発行元不明の警告が表示される場合があります。
