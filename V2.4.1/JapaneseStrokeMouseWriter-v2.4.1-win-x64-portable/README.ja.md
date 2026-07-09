# Japanese Stroke Mouse Writer V2.4.1 Internal

Windows 10/11 x64 向けのポータブル書き込みツールです。Windows SendInput を使い、日本語、英数字、一般記号、半角カタカナ、顔文字を組み立てるための中心線記号を書き込みます。

[繁體中文](README.md) / [English](README.en.md)

## インストール方法

V2.4.1 は内部開発版です。GitHub Release、タグ、ZIP は作成しません。このリポジトリ内の未圧縮フォルダーを使用します。

1. `V2.4.1/JapaneseStrokeMouseWriter-v2.4.1-win-x64-portable/` を開きます。
2. `JapaneseStrokeMouseWriter.exe` を実行します。
3. 設定は実行フォルダー横の `user_data/settings.json` に保存されます。Registry と AppData は使用しません。

## 機能

- KanjiVG またはプロジェクト自製の中心線データで、仮名、漢字、英数字、半角カタカナ、一般記号を書き込みます。
- 半角文字は `0.5` マス、全角／幅広文字は `1` マスです。半角同士は半分の文字間隔、それ以外は完全な文字間隔を使います。
- `(^O^)`、`(≧▽≦)`、`m(_ _)m`、`(/ω＼)`、`¯\_(ツ)_/¯`、`(╯°□°)╯︵ ┻━┻` などの顔文字は、利用者が手入力または貼り付けできます。
- 顔文字の内蔵分類とフォント依存の描画は使用しません。すべての文字を中心線で1文字ずつ書き込みます。
- カラー絵文字、keycap 絵文字、ZWJ シーケンス、未対応の図像記号はマウス移動前に拒否されます。

## 対応記号

`A–Z`、`a–z`、`0–9`、全角英数字、`ｶﾞ` のような半角カタカナ濁音、表示可能な ASCII 記号と全角対応（例：`#＃`、`(（`、`)）`、`[［`、`]］`、`@＠`、`~～`）に対応します。日本語記号は `、､`、`。｡`、`・･`、`ーｰ`、`「」`、`【】`、`｢｣` を含みます。

V2.4.1 では顔文字を組み立てやすい中心線記号も追加しました。完全な一覧は [V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md](V2.4.1/SUPPORTED_EMOTICON_SYMBOLS.md) を参照してください。

## コード署名

SignPath Foundation の申請は承認されませんでした。現在のビルドは未署名で、正式な署名導入フローはありません。Windows SmartScreen が発行元不明の警告を表示する場合があります。

## ライセンス

プロジェクトのコードと自製中心線 SVG は MIT License です。KanjiVG データは CC BY-SA 3.0 のままです。詳しくは [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。
