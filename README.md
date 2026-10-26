# OKAWARI Tools

面倒な操作を、もっと簡単に。Windows向けの無料ツールを配布する静的サイトと、第1弾アプリ QuickShot です。

## 構成

```
OKAWARI-Tools/
├─ website/          公開用の静的サイト
├─ quickshot/        QuickShot のソースとビルド手順
├─ releases/         バージョン付き EXE と SHA-256
└─ README.md
```

アプリ本体のソースは独自実装です。実行時の追加ライブラリはありません。EXE には Python ランタイムと PyInstaller のブートローダーが含まれます。

## QuickShot 1.1.16

公開中の版は 1.1.16 です。ダウンロードと導入手順は `https://okawari-tools.pages.dev/quickshot.html` にあります。配布EXEは GitHub Releases の `quickshot-1.1.16` です。

- ファイル: `releases/QuickShot-1.1.16-win64.exe`
- サイズ: 11,182,287 bytes
- SHA-256: `39D43D03524698174EB14B978AEA1682B571757D702AEC25C303305FCEED4484`

このEXEはコード署名をしていません。実行する前に、公開ページのSHA-256と手元のファイルを比べてください。

バージョンを上げるときは `quickshot/main.py` の `VERSION`、`quickshot/extension/manifest.json`、`quickshot/build.bat`、`website/catalog.js` を同じ番号にします。確認は `py -3 website/check_site.py` です。

画面の範囲、画面全体、ページ全体、ChatGPTの会話をPNGで保存します。ページ全体と会話の撮影には、ChromeまたはEdgeの拡張機能が必要です。拡張機能はChromeウェブストアでは公開していません。導入手順は公開ページにあります。

### ソースから起動

Python 3.12（64ビット）と Windows 10/11 が必要です。

```bat
cd quickshot
pyw -3 main.py
```

### 再ビルド

```bat
cd quickshot
build.bat
```

`build.bat` は、同じファイル名のEXEが `releases` にあると中止します。過去のEXEは削除しません。

## サイト

公開URLは `https://okawari-tools.pages.dev` です。Cloudflare Pages の出力ディレクトリは `website`、ビルドコマンドは空です。EXEはPagesに置かず、GitHub Releasesに置きます。

ダウンロード先、バージョン、サイズ、SHA-256は `website/catalog.js` が元です。`py -3 website/check_site.py` が、アプリ、拡張機能、EXE、ページ内リンク、sitemapを照合します。

新しいツールを追加するときは、`catalog.js` に項目を足し、製品ページを `website` に置き、`sitemap.xml` にURLを追加してから `check_site.py` を実行します。

連絡先は未設定です。広告ユニットは表示していません。所有確認用のAdSenseメタタグだけがあります。

## テスト結果（2026-10-17、この PC）

OS は Windows 11（10.0.26300）。モニターは 1920x1080（96 DPI）と 1920x1080（144 DPI）です。

確認できたこと:

- 24bit DIB の幅・高さ・サイズ
- 表示中のウィンドウは撮影でき、隠したあとは写らない
- クリップボードへ CF_DIB でコピーできる（テスト後、元のクリップボードは戻した）
- 常駐ボタンの表示、モニター内への配置、最前面用のキャプチャ除外 API
- ドラッグ後の位置保存、言語の保存
- 範囲選択が仮想画面全体（この PC では 3840x1155）を覆う
- 選択中はボタンが非表示、Esc で戻り、二重の選択は始まらない
- 選択完了後にボタンが戻り、CF_DIB がクリップボードにある
- 二重起動のミューテックス、EXE の起動、2つ目は通知を出して終了コード 2
- EXE が 64ビットのウィンドウサブシステムである
- サイトのトップ、QuickShot、プライバシー、利用規約、日英切り替え
- ダウンロードリンクが実ファイルを指し、サイズと SHA-256 が実測と一致する
- ページ内リンクの実在、外部リソースを読んでいないこと
- 幅 390px で横スクロールが出ず、ダウンロードボタンが押しやすい高さになること

未確認:

- ChatGPT、LINE、Discord への実際の貼り付け
- 人がマウスで範囲をドラッグした見た目と、150% 側モニターでの目視確認
- エクスプローラーから開いたときの SmartScreen 表示
- Windows 10 実機
- 実機のスマートフォン（幅 390px のエミュレーションのみ）

## 費用

いま完成分に必須の費用はありません。

任意の費用は、ドメインを取る場合の登録料と、SmartScreen の警告を減らしたい場合のコード署名証明書です。金額は事業者ごとに違うため、ここには書きません。静的ホスティングと GitHub は、各サービスの無料枠で始められることが多いです。公開前に条件を確認してください。広告は未導入です。

## バージョン更新前のバックアップ

QuickShot や ImagePort を更新する前に、その時点のソース、設定、完成版 EXE をアプリごとの `backups` フォルダへコピーする。フォルダ名はバージョン番号と日時にする。コピーのハッシュが元と一致してから修正を始める。バックアップの中は変更しない。完成版 EXE とバックアップは Git に含めず、ローカルに残す。新しい版ができても、以前の EXE とバックアップは削除しない。
