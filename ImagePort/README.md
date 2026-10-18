# ImagePort 1.0

Windows向けの無料画像一括変換・圧縮ツールです。インストールは不要です。

画像をドロップして「変換する」を押すと、元画像と同じフォルダの中に `ImagePort` フォルダを作り、そこへ保存します。元のファイルは上書きも削除もしません。

## 起動

```bat
pyw -3 main.py
```

完成版 EXE は `releases\ImagePort-1.0.1-win64.exe` です。ダブルクリックで起動します。`releases\ImagePort-1.0-win64.exe` は修正前の版として残しています。

## 開発方針

- 読み込み、変換、保存、画面は別のモジュールに分ける。
- 対応形式は `imageport/formats.py` に追加する。HEIC、HEIF、AVIF、SVG、RAW は今回実装しない。
- 設定は `%APPDATA%\ImagePort\settings.json` に保存し、`settings_version` を持つ。未知の項目は読まない。
- 完成版 EXE は `releases\` にバージョン付きの名前で残す。`build.bat` は同じファイル名を上書きしない。
- バージョンと変更内容は `CHANGELOG.md` で管理する。
- 画面は日本語の単一画面のままにする。今要らない仕組みは足さない。
