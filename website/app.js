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
    meta_home: "Windows向け無料ツールの配布サイト。第1弾は、マウスだけで画面をコピーするQuickShotです。",
    meta_quickshot: "QuickShotは、マウスで選んだ範囲をクリップボードへコピーする無料のWindowsアプリです。",
    meta_privacy: "OKAWARI ToolsとQuickShotのプライバシーポリシー。現在の実装に基づきます。",
    meta_terms: "OKAWARI ToolsとQuickShotの利用規約。",
    hero_title: "1つの面倒を、1クリックで解決する",
    hero_lead: "Windows向けの無料ツールです。登録なしで使えます。",
    tools_heading: "ツール",
    status_live: "公開中",
    planned: "開発予定",
    planned_note: "まだ公開していません。ダウンロードはできません。",
    card_summary: "マウスで範囲を選ぶと、画像がクリップボードにコピーされます。",
    card_b1: "保存画面も編集画面も開きません。",
    card_b2: "無料で、会員登録は不要です。",
    card_b3: "撮影にキーボードショートカットは不要です。",
    card_link: "無料でダウンロード",
    qs_lead: "画面の範囲をマウスで選ぶと、その画像をクリップボードへコピーします。保存や編集の画面は出ません。",
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
    f1: "マウスで範囲を選ぶだけです。",
    f2: "撮影後、画像は自動でクリップボードにコピーされます。",
    f3: "保存画面も編集画面も開きません。",
    f4: "撮影にキーボードショートカットは不要です。中止するときは Esc を押せます。",
    f5: "無料で、会員登録は不要です。",
    f6: "Windows 10 / 11 の64ビットに対応しています。",
    howto_heading: "使い方",
    s1: "QuickShotを起動します。",
    s2: "マウスで撮影範囲を選びます。カメラボタンをクリックし、ドラッグして離すとコピーされます。",
    s3: "コピーされた画像を、貼り付け先で Ctrl+V します。",
    release_link: "GitHub Releasesでファイルを確認",
    smartscreen: "このEXEにはデジタル署名がありません。初めて起動するとき、Windows SmartScreenが「WindowsによってPCが保護されました」と表示することがあります。「詳細情報」を開き、「実行」を選んでください。",
    shot_note: "アプリの画面は、実物の画像ができてからここに掲載します。",
    about_title: "運営者情報",
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
    spec_net: "アプリは外部と通信しません",
    spec_account_label: "アカウント",
    spec_account: "不要",
    spec_ads_label: "広告",
    spec_ads: "アプリ内広告なし。撮影ごとの広告なし",
    install_heading: "起動方法",
    i1: "ダウンロードしたEXEを、任意のフォルダに保存します。",
    i2: "EXEをダブルクリックして起動します。",
    i3: "「WindowsによってPCが保護されました」と出た場合は、「詳細情報」を開いて「実行」を選びます。この初期版はコード署名をしていないため、表示されることがあります。",
    i4: "管理者権限や、別のインストール作業は不要です。",
    uninstall_heading: "終了と削除",
    u1: "カメラボタンを右クリックし、「終了」を選びます。",
    u2: "保存したEXEを削除します。",
    u3: "ボタン位置などの設定も消すときは、%APPDATA%\\OKAWARI\\QuickShot フォルダを削除します。スタートアップやレジストリへの登録は行いません。",
    security_heading: "セキュリティ上の注意",
    sec1: "スクリーンショットはファイルに保存せず、パソコンのメモリとクリップボードだけで扱います。",
    sec2: "開発者のサーバーへ画像や利用状況を送りません。",
    sec3: "自動更新機能はありません。アプリが自分で別のプログラムを取りに行くことはありません。",
    sec4: "公開されているSHA-256と、手元のファイルの値が一致することを確認してください。",
    sec5: "入手元のわからないコピーは実行しないでください。",
    faq_heading: "よくある質問",
    q1: "画像はどこに保存されますか？",
    a1: "ファイルには保存しません。クリップボードにだけ入ります。その後で別の内容をコピーすると、置き換わります。",
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
    privacy_updated: "2026年10月17日 更新",
    privacy_intro: "このポリシーは、現在のOKAWARI Toolsウェブサイトと、QuickShot 1.0.1の実装について説明します。将来機能を変える場合は、このページを更新します。",
    privacy_h_site: "ウェブサイト",
    privacy_site: "このサイトは静的なHTMLです。会員登録、ログイン、アクセス解析、広告タグはありません。外部のフォントや外部スクリプトは読み込みません。表示言語の選択は、ブラウザの localStorage（キー名 okawari-lang）にだけ保存されます。この値を当方のサーバーへ送る機能はありません。",
    privacy_h_app: "QuickShot",
    privacy_app: "アカウント登録はありません。スクリーンショットはファイルとして保存せず、選択した範囲の画像をWindowsのクリップボードへコピーします。画像はアプリのメモリ上で処理し、開発者や外部のサーバーへは送信しません。常駐ボタンの位置と言語は、お使いのパソコンの %APPDATA%\\OKAWARI\\QuickShot\\settings.json に保存します。アプリに自動更新はなく、起動後に外部と通信しません。",
    privacy_h_clip: "クリップボード",
    privacy_clip: "コピーされた画像は、Windowsの仕組みによって、利用者が貼り付け先に選んだアプリへ渡ります。QuickShotは貼り付け先を選ばず、画像の内容を記録しません。",
    privacy_h_ads: "広告",
    privacy_ads: "現在、ウェブサイトにもアプリにも広告は掲載していません。将来ウェブサイトに広告を載せる場合は、広告を見ないとダウンロードできない形にはせず、掲載前にこのポリシーへ事業者と取得される情報を追記します。",
    privacy_h_contact: "連絡先",
    privacy_contact: "公開用の連絡先は、まだ設定していません。",
    terms_updated: "2026年10月17日 更新",
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
    meta_home: "Free Windows utilities. The first tool, QuickShot, copies a screen region with the mouse.",
    meta_quickshot: "QuickShot is a free Windows app that copies a mouse-selected screen region to the clipboard.",
    meta_privacy: "Privacy policy for OKAWARI Tools and QuickShot, based on the current implementation.",
    meta_terms: "Terms of use for OKAWARI Tools and QuickShot.",
    hero_title: "One hassle, one click.",
    hero_lead: "Free tools for Windows. No account required.",
    tools_heading: "Tools",
    status_live: "Available",
    planned: "Planned",
    planned_note: "Not published yet. There is no download.",
    card_summary: "Select a region with the mouse and the image is copied to the clipboard.",
    card_b1: "No save dialog and no editor.",
    card_b2: "Free, and no account required.",
    card_b3: "No keyboard shortcut is required to capture.",
    card_link: "Download free",
    qs_lead: "Select a region with the mouse and the image is copied to the clipboard. There is no save dialog and no editor.",
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
    f1: "Select a region with the mouse.",
    f2: "The image is copied to the clipboard automatically.",
    f3: "No save dialog and no editor opens.",
    f4: "No keyboard shortcut is required to capture. Press Esc to cancel.",
    f5: "Free, and no account required.",
    f6: "For 64-bit Windows 10 and Windows 11.",
    howto_heading: "How to use",
    s1: "Start QuickShot.",
    s2: "Select the area with the mouse. Click the camera button, drag, and release to copy.",
    s3: "Paste the copied image with Ctrl+V.",
    release_link: "Check the file on GitHub Releases",
    smartscreen: "This EXE is not digitally signed. On first launch, Windows SmartScreen may say “Windows protected your PC”. Open More info and choose Run anyway.",
    shot_note: "An app image will be added here when a real screenshot is available.",
    about_title: "About",
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
    spec_net: "The app does not contact the network",
    spec_account_label: "Account",
    spec_account: "Not required",
    spec_ads_label: "Ads",
    spec_ads: "No in-app ads and no ad after each capture",
    install_heading: "How to start",
    i1: "Save the downloaded EXE in any folder.",
    i2: "Double-click the EXE.",
    i3: "If Windows shows “Windows protected your PC”, open “More info” and choose “Run anyway”. This first build is not code-signed, so that warning can appear.",
    i4: "Administrator rights and a separate installer are not required.",
    uninstall_heading: "Exit and removal",
    u1: "Right-click the camera button and choose “Exit”.",
    u2: "Delete the EXE you saved.",
    u3: "To remove the saved button position as well, delete the %APPDATA%\\OKAWARI\\QuickShot folder. The app does not register itself for startup or write a registry entry.",
    security_heading: "Security notes",
    sec1: "Screenshots are not saved as files. They stay in memory and on the clipboard.",
    sec2: "Images and usage data are not sent to a server.",
    sec3: "There is no auto-update. The app does not download other programs.",
    sec4: "Check that the SHA-256 of your file matches the value published with the release.",
    sec5: "Do not run a copy if you do not know where it came from.",
    faq_heading: "FAQ",
    q1: "Where is the image saved?",
    a1: "It is not saved as a file. It is placed only on the clipboard. Another copy replaces it.",
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
    privacy_updated: "Updated 17 October 2026",
    privacy_intro: "This policy describes the current OKAWARI Tools website and QuickShot 1.0.1. If the software changes, this page will be updated.",
    privacy_h_site: "Website",
    privacy_site: "The site is static HTML. It has no accounts, login, analytics, or ad tags. It does not load external fonts or external scripts. The language choice is stored only in the browser localStorage key okawari-lang. Nothing on this site sends that value to a server.",
    privacy_h_app: "QuickShot",
    privacy_app: "There is no account. Screenshots are not saved as files. The selected region is copied to the Windows clipboard. Image data is handled in memory and is not sent to the developer or to any server. The button position and language are stored on the PC in %APPDATA%\\OKAWARI\\QuickShot\\settings.json. The app has no auto-update and does not use the network after it starts.",
    privacy_h_clip: "Clipboard",
    privacy_clip: "Windows passes the copied image to the app you paste into. QuickShot does not choose that destination and does not record the image.",
    privacy_h_ads: "Advertising",
    privacy_ads: "The website and the app currently show no ads. If the website adds ads later, a download will not be locked behind an ad, and this policy will be updated first with the provider and the data involved.",
    privacy_h_contact: "Contact",
    privacy_contact: "A public contact address is not set yet.",
    terms_updated: "Updated 17 October 2026",
    terms_p1: "QuickShot is free to use. No account is required.",
    terms_p2: "The tool is provided as it is. There is no warranty that it fits a particular purpose, that it will run without interruption, or that every screenshot will be complete.",
    terms_p3: "Do not use it in a way that breaks the law or infringes someone else's rights.",
    terms_p4: "You use the tool at your own responsibility.",
    terms_p5: "When you use a distributed file, check the download location and SHA-256 shown on this site. Do not run a file if you do not know where it came from.",
    terms_p6: "The software, these terms, and the privacy policy may be updated. If the Japanese and English texts differ, the Japanese text takes priority."
  }
};

// QuickShot 1.0.1 asset on GitHub Releases.
const GITHUB_RELEASE_URL = "https://github.com/mstyleworks1234-droid/OKAWARI-Tools/releases/download/quickshot-1.0.1/QuickShot-1.0.1-win64.exe";

const RELEASE = {
  version: "1.0.1",
  fileName: "QuickShot-1.0.1-win64.exe",
  bytes: 10448445,
  sha256: "4DF24466E9770808A0593D5A8B2D059C70460E81497A4AEBA88EAB800C766479",
  href: GITHUB_RELEASE_URL
};

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
