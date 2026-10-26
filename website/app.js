/* OKAWARI Tools
   Strings live in I18N. Add a language by adding an object, or later load JSON into I18N.
   RELEASE describes the QuickShot file. Leave href empty when the EXE does not exist.
   Do not invent size or checksum. A download is enabled only when href, bytes, and sha256 are all set.
   Set GITHUB_RELEASE_URL to the real GitHub Releases asset URL before publish.
*/
const I18N = {
  ja: {
    skip: "内容へスキップ",
    footer_privacy: "プライバシーポリシー",
    footer_terms: "利用規約",
    footer_about: "運営者情報",
    title_home: "OKAWARI Tools",
    title_quickshot: "QuickShot - OKAWARI Tools",
    title_privacy: "プライバシーポリシー - OKAWARI Tools",
    title_terms: "利用規約 - OKAWARI Tools",
    title_404: "ページが見つかりません - OKAWARI Tools",
    meta_404: "指定されたページは見つかりません。ツール一覧から目的のページを開けます。",
    missing_heading: "ページが見つかりません",
    meta_home: "Windows向けの無料ツール OKAWARI Tools。QuickShotは画面、ページ全体、ChatGPTの会話をPNGで保存できます。",
    meta_quickshot: "QuickShot 1.1.16は、Windowsで画面、ページ全体、ChatGPTの会話をPNGで保存できる無料アプリです。",
    meta_privacy: "OKAWARI ToolsとQuickShotのプライバシーポリシー。現在の実装に基づきます。",
    meta_terms: "OKAWARI ToolsとQuickShotの利用規約。",
    hero_title: "1つの面倒を、1クリックで解決する",
    hero_lead: "Windows向けの無料ツールです。登録なしで使えます。",
    tools_heading: "ツール",
    status_live: "公開中",
    planned: "開発予定",
    planned_note: "まだ公開していません。ダウンロードはできません。",
    card_summary: "画面の範囲、画面全体、ページ全体、ChatGPTの会話をPNGで保存できます。",
    card_b1: "保存画面も編集画面も開きません。",
    card_b2: "無料で、会員登録は不要です。",
    card_b3: "撮影にキーボードショートカットは不要です。",
    card_link: "無料でダウンロード",
    qs_lead: "画面の撮影に加え、ブラウザ拡張機能でページ全体とChatGPTの会話を保存できます。文字認識と簡単な編集もアプリ内で行えます。",
    badge_free: "無料",
    badge_win: "Windows",
    download: "無料でダウンロード",
    download_pending: "ダウンロードはまだ利用できません",
    download_note: "会員登録は不要です。ボタンからEXEを保存できます。",
    download_note_pending: "配布用EXEがまだ無いため、ダウンロードは無効です。",
    version_label: "アプリのバージョン",
    size_label: "ファイルサイズ",
    hash_label: "SHA-256",
    file_label: "ファイル名",
    size_unknown: "未計測",
    hash_unknown: "未計測",
    file_unknown: "—",
    features_heading: "主な特徴",
    f1: "範囲指定、画面全体、ページ全体を撮影できます。",
    f2: "画像はPNGで保存します。初期設定ではクリップボードにもコピーします。",
    f3: "保存した画像の文字認識と、切り抜きやモザイクなどの簡単な編集ができます。",
    f4: "ページ全体とChatGPTの会話撮影には、ChromeまたはEdgeの拡張機能が必要です。",
    f5: "無料で、会員登録は不要です。",
    f6: "Windows 10 / 11 の64ビットに対応しています。",
    howto_heading: "使い方",
    s1: "QuickShotを起動します。画面端に操作パネルが出ます。",
    s2: "範囲指定、画面全体、または拡張機能が接続されたページ撮影を選びます。",
    s3: "画像は保存先のフォルダにPNGで保存されます。初期設定ではクリップボードにもコピーされます。",
    release_link: "GitHub Releasesでファイルを確認",
    smartscreen: "このEXEにはデジタル署名がありません。初めて起動するとき、Windowsが「WindowsによってPCが保護されました」と表示することがあります。表示内容を確認し、このサイトのSHA-256と手元のファイルが一致する場合にのみ、実行するかどうかを判断してください。",
    shot_note: "アプリの画面は、実物の画像ができてからここに掲載します。",
    about_title: "運営者情報",
    meta_about: "OKAWARI Toolsの運営者情報です。連絡先は未設定です。",
    about_p1: "このサイトの運営者は OKAWARI Tools です。Windows向けの無料ツールを公開しています。",
    about_p2: "公開用の連絡先は、まだ設定していません。",
    spec_heading: "仕様",
    spec_os_label: "対応OS",
    spec_os: "Windows 10 / 11（64ビット）",
    spec_arch_label: "形式",
    spec_arch: "単体EXE（インストール不要）",
    spec_price_label: "料金",
    spec_price: "無料",
    spec_net_label: "通信",
    spec_net: "画像を開発者のサーバーへ送りません。拡張機能との通信は同じパソコンの中だけです",
    spec_account_label: "アカウント",
    spec_account: "不要",
    spec_ads_label: "広告",
    spec_ads: "アプリ内広告なし。撮影ごとの広告なし",
    install_heading: "起動方法",
    i1: "ダウンロードしたEXEを、任意のフォルダに保存します。",
    i2: "EXEをダブルクリックして起動します。",
    i3: "「WindowsによってPCが保護されました」と出た場合は、表示内容とSHA-256を確認してから、実行するかどうかを判断します。この版はコード署名をしていないため、警告が出ることがあります。",
    i4: "管理者権限や、別のインストール作業は不要です。",
    uninstall_heading: "終了と削除",
    u1: "パネルを右クリックし、「終了」を選びます。",
    u2: "保存したEXEを削除します。ChromeまたはEdgeに読み込んだ拡張機能も削除します。",
    u3: "設定や履歴も消すときは、%APPDATA%\\OKAWARI\\QuickShot フォルダを削除します。Native Messagingの登録は、ChromeとEdgeの現在のユーザーのレジストリに残ります。",
    security_heading: "セキュリティ上の注意",
    sec1: "画像はパソコン内にPNGで保存されます。初期の保存先はピクチャの QuickShot フォルダで、設定から変更できます。",
    sec2: "開発者のサーバーへ画像や利用状況を送りません。",
    sec3: "自動更新機能はありません。アプリが自分で別のプログラムを取りに行くことはありません。",
    sec4: "公開されているSHA-256と、手元のファイルの値が一致することを確認してください。",
    sec5: "入手元のわからないコピーは実行しないでください。",
    faq_heading: "よくある質問",
    q1: "画像はどこに保存されますか？",
    a1: "範囲指定、画面全体、ページ全体、会話撮影の画像はPNGで保存されます。初期設定では撮影後にクリップボードへもコピーします。長いページは複数のPNGに分かれることがあります。",
    q2: "料金はかかりますか？",
    a2: "QuickShotの利用に料金はありません。アカウントも不要です。アプリの中に広告は出ません。",
    q3: "どのWindowsで使えますか？",
    a3: "Windows 10およびWindows 11の64ビットを対象にしています。",
    q4: "ボタンがスクリーンショットに写りますか？",
    a4: "撮影の直前にボタンを隠し、コピーが終わってから戻します。",
    q5: "どうやって終了しますか？",
    a5: "カメラボタンを右クリックして「終了」を選びます。",
    q6: "2回起動するとどうなりますか？",
    a6: "2つ目は起動しません。すでに起動していることを知らせる画面を表示します。",
    q7: "再起動したあとは自動で立ち上がりますか？",
    a7: "自動起動はしません。使うときにEXEを開いてください。ボタンの位置はパソコン内に保存されています。",
    back_home: "ツール一覧へ",
    privacy_updated: "2026年10月26日 更新",
    privacy_intro: "このポリシーは、現在のOKAWARI Toolsウェブサイトと、QuickShot 1.1.16の実装について説明します。将来機能を変える場合は、このページを更新します。",
    privacy_h_site: "ウェブサイト",
    privacy_site: "このサイトは静的なHTMLです。会員登録、ログイン、アクセス解析はありません。サイト所有の確認用に Google AdSense のアカウントメタタグを置いています。広告ユニットは表示していません。外部のフォントや外部スクリプトは読み込みません。表示言語の選択は、ブラウザの localStorage（キー名 okawari-lang）にだけ保存されます。この値を当方のサーバーへ送る機能はありません。",
    privacy_h_app: "QuickShot",
    privacy_app: "アカウント登録はありません。撮影した画像は、お使いのパソコン内にPNGで保存します。初期の保存先はピクチャの QuickShot フォルダで、設定から変更できます。初期設定ではクリップボードにもコピーします。画像は開発者や外部のサーバーへ送信しません。ボタンの位置、言語、保存先は %APPDATA%\\OKAWARI\\QuickShot\\settings.json に保存します。撮影履歴も同じフォルダ内に残ります。操作ログは同じフォルダの quickshot.log に残り、開発者のサーバーへは送りません。ログには操作の成否に加え、拡張機能が接続しているときのサイトのホスト名とパスが入ることがあります。会話の本文やCookieは記録しません。アプリに自動更新はありません。",
    privacy_h_ext: "拡張機能",
    privacy_ext: "ページ全体とChatGPT会話の撮影には、ChromeまたはEdgeの拡張機能を使います。この拡張機能はChromeウェブストアでは配布していません。拡張機能は同じパソコンで起動しているQuickShotとだけ通信します。通信先は開発者のサーバーではありません。初回起動時に、現在のユーザーのレジストリへ Native Messaging の登録を行います。",
    privacy_h_clip: "クリップボード",
    privacy_clip: "コピーされた画像は、Windowsの仕組みによって、利用者が貼り付け先に選んだアプリへ渡ります。QuickShotは貼り付け先を選ばず、画像の内容を記録しません。",
    privacy_h_ads: "広告",
    privacy_ads: "現在、ウェブサイトに広告ユニットは表示していません。アプリ内にも広告はありません。所有確認用のメタタグは広告の配信ではありません。将来ウェブサイトに広告を載せる場合は、広告を見ないとダウンロードできない形にはせず、掲載前にこのポリシーへ事業者と取得される情報を追記します。",
    privacy_h_contact: "連絡先",
    privacy_contact: "公開用の連絡先は、まだ設定していません。",
    terms_updated: "2026年10月26日 更新",
    limits_heading: "既知の制限",
    lim1: "このEXEにはコード署名がありません。Windowsが警告を出すことがあります。このサイトのSHA-256と手元のファイルが一致することを確認し、実行するかどうかはご自身で判断してください。",
    lim2: "Chrome拡張機能はChromeウェブストアでは公開していません。読み込みには開発者モードが必要です。",
    lim3: "ページ全体と会話撮影は、拡張機能が接続されているChromeまたはEdgeだけで使えます。",
    lim4: "ChatGPTの画面構造が変わると、会話領域を見つけられないことがあります。見つからない場合は、ページ全体の撮影には切り替えません。",
    lim5: "非常に長いページは複数のPNGに分割します。分割の境界で行が分かれることがあります。撮影を完了できない場合はエラーを表示します。",
    lim6: "文字認識はWindowsの機能を使います。日本語または英語の言語パックが無いと、その言語は認識できません。",
    ext_heading: "Chrome拡張機能",
    ext1: "QuickShotのEXEを一度起動します。同じパソコンの中に拡張機能のファイルとNative Messagingの登録が作られます。",
    ext2: "ChromeまたはEdgeで拡張機能の管理画面を開きます。",
    ext3: "開発者モードをオンにします。",
    ext4: "%APPDATA%\\OKAWARI\\QuickShot\\extension フォルダを、「パッケージ化されていない拡張機能を読み込む」で指定します。",
    ext5: "QuickShotを起動したまま、撮影したいページを開きます。パネルからページ全体またはChatGPT会話を選びます。",
    ext6: "拡張機能を更新したあとは、管理画面で再読み込みが必要です。EXEを別の場所へ移した場合は、もう一度起動してください。",
    changelog_heading: "更新履歴",
    cl1: "1.1.16：ChatGPTの会話撮影で、画面下の入力欄が分割画像に写り込まないようにしました。",
    cl2: "1.1.12以降：保全ソースでは、長いページを複数のPNGに分けて保存できます。",
    cl3: "1.1.8：文字認識、簡単な編集、撮影履歴、ショートカットを追加しました。",
    cl4: "1.0.1：範囲指定の撮影を公開しました。",
    old_heading: "過去のバージョン",
    old_note: "通常は最新版の使用をおすすめします。過去のバージョンは互換性確認や旧機能の利用などを目的として提供しています。",
    old_built: "ファイルの日付",
    old_published: "配布開始",
    old_download: "このバージョンをダウンロード",
    old_limits: "コード署名はありません。最新版より機能が少ないことや、後の版で直した不具合が残っていることがあります。",
    compare_heading: "機能の比較",
    compare_note: "「あり」は、その版のリリースノート、または同じバージョン番号の保全ソースに機能があることです。実機で常に成功することは意味しません。表にない版は、各バージョンの説明を見てください。",
    compare_feature: "機能",
    cmp_area: "範囲指定",
    cmp_screen: "画面全体",
    cmp_page: "ページ全体",
    cmp_chat: "ChatGPT会話",
    cmp_split: "長文の複数PNG",
    cmp_ocr: "文字認識",
    cmp_edit: "画像編集",
    cmp_extension: "拡張機能",
    cmp_yes: "あり",
    cmp_no: "なし",
    q8: "拡張機能はどこから入手しますか？",
    a8: "Chromeウェブストアにはありません。EXEを起動したあと、アプリがパソコン内に置いた extension フォルダを開発者モードで読み込みます。同じファイルのZIPもGitHub Releasesにあります。",
    terms_p1: "QuickShotは無料で利用できます。会員登録は不要です。",
    terms_p2: "ツールは現状のまま提供します。特定の目的に合うこと、動作が中断しないこと、スクリーンショットが常に欠けることなく撮れることは保証しません。",
    terms_p3: "法令に反する用途や、他者の権利を侵害する用途には使用しないでください。",
    terms_p4: "ツールの利用は、利用者の責任で行ってください。",
    terms_p5: "配布ファイルを使うときは、このサイトで案内する入手先とSHA-256を確認し、入手元が不明なファイルは実行しないでください。",
    terms_p6: "機能、本規約、プライバシーポリシーは更新されることがあります。日本語と英語の記載に違いがあるときは、日本語の記載を優先します。"
  },
  en: {
    skip: "Skip to content",
    footer_privacy: "Privacy policy",
    footer_terms: "Terms",
    footer_about: "About",
    title_home: "OKAWARI Tools",
    title_quickshot: "QuickShot - OKAWARI Tools",
    title_privacy: "Privacy policy - OKAWARI Tools",
    title_terms: "Terms - OKAWARI Tools",
    title_404: "Page not found - OKAWARI Tools",
    meta_404: "That page was not found. You can return to the tool list.",
    missing_heading: "Page not found",
    meta_home: "Free Windows tools from OKAWARI Tools. QuickShot saves the screen, a full page, or a ChatGPT conversation as PNG files.",
    meta_quickshot: "QuickShot 1.1.16 is a free Windows app that saves the screen, a full page, or a ChatGPT conversation as PNG files.",
    meta_privacy: "Privacy policy for OKAWARI Tools and QuickShot, based on the current implementation.",
    meta_terms: "Terms of use for OKAWARI Tools and QuickShot.",
    hero_title: "One hassle, one click.",
    hero_lead: "Free tools for Windows. No account required.",
    tools_heading: "Tools",
    status_live: "Available",
    planned: "Planned",
    planned_note: "Not published yet. There is no download.",
    card_summary: "Save a selected area, the whole screen, a full web page, or a ChatGPT conversation as PNG files.",
    card_b1: "No save dialog and no editor.",
    card_b2: "Free, and no account required.",
    card_b3: "No keyboard shortcut is required to capture.",
    card_link: "Download free",
    qs_lead: "Capture the screen, and use a browser extension to save a full page or a ChatGPT conversation. Text recognition and a simple editor are included.",
    badge_free: "Free",
    badge_win: "Windows",
    download: "Download free",
    download_pending: "Download is not available yet",
    download_note: "No account is required. The button saves the EXE.",
    download_note_pending: "The download stays disabled until a release EXE exists.",
    version_label: "App version",
    size_label: "File size",
    hash_label: "SHA-256",
    file_label: "File name",
    size_unknown: "Not measured",
    hash_unknown: "Not measured",
    file_unknown: "—",
    features_heading: "Features",
    f1: "Capture a selected area, the whole screen, or a full page.",
    f2: "Images are saved as PNG files. With the default setting they are also copied to the clipboard.",
    f3: "Recognize text in a saved image, and crop or pixelate it in the simple editor.",
    f4: "Full-page and ChatGPT conversation capture need the Chrome or Edge extension.",
    f5: "Free, and no account required.",
    f6: "For 64-bit Windows 10 and Windows 11.",
    howto_heading: "How to use",
    s1: "Start QuickShot. A small panel appears at the edge of the screen.",
    s2: "Choose an area, the whole screen, or a page capture while the extension is connected.",
    s3: "The PNG is saved in the destination folder. The default setting also copies it to the clipboard.",
    release_link: "Check the file on GitHub Releases",
    smartscreen: "This EXE is not digitally signed. Windows may say that it protected your PC. Read the warning, and run the file only after its SHA-256 matches the value on this site. You decide whether to run it.",
    shot_note: "An app image will be added here when a real screenshot is available.",
    about_title: "About",
    meta_about: "About OKAWARI Tools. A public contact address is not set yet.",
    about_p1: "This site is published by OKAWARI Tools. It offers free tools for Windows.",
    about_p2: "A public contact address is not set yet.",
    spec_heading: "Specifications",
    spec_os_label: "OS",
    spec_os: "Windows 10 / 11 (64-bit)",
    spec_arch_label: "Package",
    spec_arch: "Single EXE (no installer)",
    spec_price_label: "Price",
    spec_price: "Free",
    spec_net_label: "Network",
    spec_net: "Images are not sent to the developer. The extension talks only to QuickShot on the same PC",
    spec_account_label: "Account",
    spec_account: "Not required",
    spec_ads_label: "Ads",
    spec_ads: "No in-app ads and no ad after each capture",
    install_heading: "How to start",
    i1: "Save the downloaded EXE in any folder.",
    i2: "Double-click the EXE.",
    i3: "If Windows shows a protection warning, check the message and the SHA-256 before you decide whether to run the file. This build is not code-signed, so the warning can appear.",
    i4: "Administrator rights and a separate installer are not required.",
    uninstall_heading: "Exit and removal",
    u1: "Right-click the panel and choose Exit.",
    u2: "Delete the EXE, and remove the extension from Chrome or Edge.",
    u3: "To remove settings and history, delete the %APPDATA%\\OKAWARI\\QuickShot folder. The Native Messaging registry entries for the current user remain until you delete them.",
    security_heading: "Security notes",
    sec1: "Images are saved as PNG files on the PC. The default folder is QuickShot inside Pictures, and it can be changed in settings.",
    sec2: "Images and usage data are not sent to a server.",
    sec3: "There is no auto-update. The app does not download other programs.",
    sec4: "Check that the SHA-256 of your file matches the value published with the release.",
    sec5: "Do not run a copy if you do not know where it came from.",
    faq_heading: "FAQ",
    q1: "Where is the image saved?",
    a1: "Area, full-screen, full-page, and conversation captures are saved as PNG files. The default setting also copies the image to the clipboard. A long page can be split across several PNG files.",
    q2: "Does it cost anything?",
    a2: "QuickShot is free. No account is required, and the app shows no ads.",
    q3: "Which version of Windows?",
    a3: "Windows 10 and Windows 11, 64-bit.",
    q4: "Does the button appear in the screenshot?",
    a4: "The button is hidden just before the capture and shown again after the copy.",
    q5: "How do I quit?",
    a5: "Right-click the camera button and choose Exit.",
    q6: "What if I start it twice?",
    a6: "The second start does nothing except tell you that QuickShot is already running.",
    q7: "Does it start after a reboot?",
    a7: "No. Open the EXE when you want it. The button position is saved on the PC.",
    back_home: "All tools",
    privacy_updated: "Updated 26 October 2026",
    privacy_intro: "This policy describes the current OKAWARI Tools website and QuickShot 1.1.16. If the software changes, this page will be updated.",
    privacy_h_site: "Website",
    privacy_site: "The site is static HTML. It has no accounts, login, or analytics. A Google AdSense account meta tag is present for site verification. No ad unit is displayed. The site does not load external fonts or external scripts. The language choice is stored only in the browser localStorage key okawari-lang. Nothing on this site sends that value to a server.",
    privacy_h_app: "QuickShot",
    privacy_app: "There is no account. Captured images are saved as PNG files on your PC. The default folder is QuickShot inside Pictures, and you can change it. The default setting also copies the image to the clipboard. Images are not sent to the developer or to any other server. The button position, language, and save folder are stored in %APPDATA%\\OKAWARI\\QuickShot\\settings.json. Capture history stays in that folder. An operation log is stored there as quickshot.log and is not uploaded. The log can include the result of an operation and, while the extension is connected, the host and path of the active site. It does not record conversation text or cookies. The app has no auto-update.",
    privacy_h_ext: "Extension",
    privacy_ext: "Full-page and ChatGPT conversation capture use a Chrome or Edge extension. The extension is not distributed through the Chrome Web Store. It talks only to QuickShot running on the same PC, not to the developer's server. The first launch registers a Native Messaging host in the current user's registry.",
    privacy_h_clip: "Clipboard",
    privacy_clip: "Windows passes the copied image to the app you paste into. QuickShot does not choose that destination and does not record the image.",
    privacy_h_ads: "Advertising",
    privacy_ads: "The website does not currently display an ad unit, and the app shows no ads. The verification meta tag does not serve ads. If the website adds ads later, a download will not be locked behind an ad, and this policy will be updated first with the provider and the data involved.",
    privacy_h_contact: "Contact",
    privacy_contact: "A public contact address is not set yet.",
    terms_updated: "Updated 26 October 2026",
    limits_heading: "Known limits",
    lim1: "This EXE is not code-signed. Windows may show a warning. Compare the SHA-256 on this site with your file, and decide for yourself whether to run it.",
    lim2: "The Chrome extension is not published on the Chrome Web Store. Loading it requires developer mode.",
    lim3: "Full-page and conversation capture work only in Chrome or Edge while the extension is connected.",
    lim4: "If the ChatGPT page structure changes, QuickShot may not find the conversation. It does not then capture the whole page instead.",
    lim5: "A very long page is split into several PNG files. A split can fall in the middle of a line. If a capture cannot finish, QuickShot shows an error.",
    lim6: "Text recognition uses Windows. A language cannot be recognized when its Windows language pack is not installed.",
    ext_heading: "Chrome extension",
    ext1: "Start the QuickShot EXE once. It places the extension files on the PC and registers Native Messaging.",
    ext2: "Open the extensions page in Chrome or Edge.",
    ext3: "Turn on developer mode.",
    ext4: "Choose Load unpacked and select the %APPDATA%\\OKAWARI\\QuickShot\\extension folder.",
    ext5: "Keep QuickShot running, open the page you want, and choose full-page or ChatGPT conversation capture from the panel.",
    ext6: "After an extension update, reload it on the extensions page. If you move the EXE, start it once more.",
    changelog_heading: "Updates",
    cl1: "1.1.16: ChatGPT conversation capture no longer stitches the bottom input field into a split image.",
    cl2: "1.1.12 and later: the preserved source can save a long page as several PNG files.",
    cl3: "1.1.8: text recognition, a simple editor, capture history, and shortcuts were added.",
    cl4: "1.0.1: area capture was published.",
    old_heading: "Earlier versions",
    old_note: "The latest version is recommended. Earlier versions are provided for compatibility checks and for using older behavior.",
    old_built: "File date",
    old_published: "Published",
    old_download: "Download this version",
    old_limits: "These builds are not code-signed. An older build can have fewer features, or bugs that a later version fixed.",
    compare_heading: "Feature comparison",
    compare_note: "Yes means the release note, or the preserved source with the same version number, contains the feature. It does not mean every capture succeeded on a real machine. For versions that are not columns here, read that version's description.",
    compare_feature: "Feature",
    cmp_area: "Selected area",
    cmp_screen: "Full screen",
    cmp_page: "Full web page",
    cmp_chat: "ChatGPT conversation",
    cmp_split: "Long capture as several PNGs",
    cmp_ocr: "Text recognition",
    cmp_edit: "Image editor",
    cmp_extension: "Browser extension",
    cmp_yes: "Yes",
    cmp_no: "No",
    q8: "Where do I get the extension?",
    a8: "It is not on the Chrome Web Store. After you start the EXE, load the extension folder it places on the PC, using developer mode. The same files are also attached as a ZIP on GitHub Releases.",
    terms_p1: "QuickShot is free to use. No account is required.",
    terms_p2: "The tool is provided as it is. There is no warranty that it fits a particular purpose, that it will run without interruption, or that every screenshot will be complete.",
    terms_p3: "Do not use it in a way that breaks the law or infringes someone else's rights.",
    terms_p4: "You use the tool at your own responsibility.",
    terms_p5: "When you use a distributed file, check the download location and SHA-256 shown on this site. Do not run a file if you do not know where it came from.",
    terms_p6: "The software, these terms, and the privacy policy may be updated. If the Japanese and English texts differ, the Japanese text takes priority."
  }
};

const RELEASE = CATALOG.tools.find((tool) => tool.id === "quickshot");

const LANG_KEY = "okawari-lang";

function detectLang() {
  try {
    const saved = localStorage.getItem(LANG_KEY);
    if (saved === "ja" || saved === "en") return saved;
  } catch (error) {
    /* private mode or file restrictions */
  }
  const name = (navigator.language || "ja").toLowerCase();
  return name.startsWith("ja") ? "ja" : "en";
}

let lang = detectLang();

function t(key) {
  return (I18N[lang] && I18N[lang][key]) || I18N.ja[key] || "";
}

function formatBytes(bytes) {
  const locale = lang === "ja" ? "ja-JP" : "en-US";
  const exact = bytes.toLocaleString(locale) + " bytes";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB (" + exact + ")";
  return (bytes / 1048576).toFixed(2) + " MB (" + exact + ")";
}

function releaseReady() {
  return Boolean(RELEASE.href && RELEASE.bytes && RELEASE.sha256);
}

function applyRelease() {
  const button = document.getElementById("download");
  const note = document.getElementById("download-note");
  const ready = releaseReady();
  if (button) {
    if (ready) {
      button.href = RELEASE.href;
      button.classList.remove("disabled");
      button.removeAttribute("aria-disabled");
      button.removeAttribute("role");
      button.textContent = t("download");
    } else {
      button.removeAttribute("href");
      button.classList.add("disabled");
      button.setAttribute("role", "button");
      button.setAttribute("aria-disabled", "true");
      button.textContent = t("download_pending");
    }
  }
  if (note) note.textContent = t(ready ? "download_note" : "download_note_pending");
  const version = document.getElementById("file-version");
  const size = document.getElementById("file-size");
  const hash = document.getElementById("file-hash");
  const name = document.getElementById("file-name");
  if (version) version.textContent = RELEASE.version;
  if (size) size.textContent = ready ? formatBytes(RELEASE.bytes) : t("size_unknown");
  if (hash) hash.textContent = ready ? RELEASE.sha256 : t("hash_unknown");
  if (name) name.textContent = ready ? RELEASE.fileName : t("file_unknown");
  const heading = document.getElementById("product-version");
  if (heading && RELEASE) heading.textContent = RELEASE.name + " " + RELEASE.version;
  const releasePage = document.querySelector(".release-link");
  if (releasePage && RELEASE && RELEASE.href) {
    releasePage.href = RELEASE.href.replace("/download/", "/tag/").replace(/\/[^/]+$/, "");
  }
}

function renderHistory() {
  const tool = (typeof CATALOG !== "undefined" && CATALOG.tools) ? CATALOG.tools[0] : null;
  const list = document.getElementById("old-releases");
  if (list && tool && tool.releases) {
    list.textContent = "";
    tool.releases.forEach((item) => {
      const article = document.createElement("article");
      article.className = "version-item";
      const title = document.createElement("h3");
      title.textContent = tool.name + " " + item.version;
      const meta = document.createElement("p");
      meta.className = "note";
      meta.textContent = t("old_built") + " " + item.built + " / " + t("old_published") + " " + item.published;
      const summary = document.createElement("p");
      summary.textContent = lang === "en" ? item.summaryEn : item.summaryJa;
      const limits = document.createElement("p");
      limits.className = "note";
      limits.textContent = t("old_limits");
      const link = document.createElement("p");
      const anchor = document.createElement("a");
      anchor.href = item.href;
      anchor.textContent = t("old_download") + " (" + formatBytes(item.bytes) + ")";
      link.appendChild(anchor);
      article.append(title, meta, summary, limits, link);
      list.appendChild(article);
    });
  }
  const table = document.getElementById("compare-table");
  if (table && tool && tool.compare) {
    table.textContent = "";
    const head = document.createElement("tr");
    const corner = document.createElement("th");
    corner.textContent = t("compare_feature");
    head.appendChild(corner);
    tool.compare.columns.forEach((column) => {
      const cell = document.createElement("th");
      cell.textContent = column;
      head.appendChild(cell);
    });
    table.appendChild(head);
    tool.compare.rows.forEach((row) => {
      const line = document.createElement("tr");
      const name = document.createElement("th");
      name.textContent = t("cmp_" + row.key);
      line.appendChild(name);
      row.cells.forEach((cell) => {
        const value = document.createElement("td");
        value.textContent = t(cell === "yes" ? "cmp_yes" : "cmp_no");
        line.appendChild(value);
      });
      table.appendChild(line);
    });
  }
}

function applyI18n() {
  document.documentElement.lang = lang;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const value = t(element.getAttribute("data-i18n"));
    if (value) element.textContent = value;
  });
  const titleKey = document.body.getAttribute("data-title");
  if (titleKey) document.title = t(titleKey);
  const metaKey = document.body.getAttribute("data-meta");
  const meta = document.querySelector('meta[name="description"]');
  if (meta && metaKey) meta.setAttribute("content", t(metaKey));
  const toggle = document.getElementById("lang-toggle");
  if (toggle) {
    toggle.textContent = lang === "ja" ? "English" : "日本語";
    toggle.setAttribute("aria-label", lang === "ja" ? "English" : "日本語");
  }
  applyRelease();
  renderHistory();
}

const toggle = document.getElementById("lang-toggle");
if (toggle) {
  toggle.addEventListener("click", () => {
    lang = lang === "ja" ? "en" : "ja";
    try { localStorage.setItem(LANG_KEY, lang); } catch (error) { /* ignore */ }
    applyI18n();
  });
}

const download = document.getElementById("download");
if (download) {
  download.addEventListener("click", (event) => {
    if (!releaseReady()) event.preventDefault();
  });
}

applyI18n();
