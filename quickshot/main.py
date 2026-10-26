"""QuickShot: a small always-on-top button that copies a screen region."""

import capture

capture.enable_dpi_awareness()

import json
import os
import sys
import time
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

import bridge
import editor
import history
import hotkey
import imageutil
import ocr
import pngsave

VERSION = "1.1.16"

PANEL = ("select", "screen", "page", "settings", "lang", "exit")

STRINGS = {
    "ja": {
        "exit": "終了",
        "copied": "コピーしました",
        "failed": "コピーに失敗しました",
        "tip": "ドラッグで移動",
        "select": "範囲を選択して撮影",
        "select_short": "範囲",
        "screen_short": "画面",
        "page_short": "ページ",
        "settings": "設定",
        "choose_folder": "フォルダを選択",
        "open_folder": "フォルダを開く",
        "save_folder": "保存先",
        "close": "閉じる",
        "folder_failed": "フォルダを開けませんでした",
        "already": "QuickShot はすでに起動しています。",
        "screen": "画面全体を保存",
        "page": "ページ全体を保存",
        "saved_one": "画面全体を保存しました",
        "saved_many": "{n}台の画面を1枚に保存しました",
        "screen_failed": "画面全体の保存に失敗しました",
        "screen_large": "画面が広すぎて1枚に保存できません",
        "page_checking": "接続を確認しています",
        "page_start": "ページを上から撮影しています",
        "page_saved": "ページ全体を保存しました",
        "page_truncated": "ページが長いため、上から一部まで保存しました",
        "page_parts": "{n}枚に分けて最後まで保存しました",
        "chat_parts": "ChatGPTの会話を{n}枚に分けて最後まで保存しました",
        "page_parts_partial": "{n}枚まで保存しました。続きは保存できていません。",
        "parts_no_copy": "複数枚のため、クリップボードにはコピーしていません。",
        "page_too_wide": "画面が広すぎて1枚に保存できません",
        "page_partial_top": "上方向の読み込みが続いたため、読み込めた範囲だけを保存しました",
        "page_partial_bottom": "最下部まで届かなかったため、途中までの画像を保存しました",
        "page_failed": "ページ全体の撮影に失敗しました",
        "page_timeout": "ページ全体の撮影が完了しませんでした",
        "page_no_response": "拡張機能から応答がありません。QuickShot を起動したまま、拡張機能を再読み込みしてください。",
        "page_permission": "ページ全体の撮影に必要な権限がありません。拡張機能の管理で QuickShot Page Capture を再読み込みし、サイトへのアクセスを「すべてのサイト」にしてください。",
        "page_capture_timeout": "画面の取得が途中で止まったため、撮影を中断しました。ページを前面にして、もう一度試してください。",
        "cancel": "キャンセル",
        "page_setup_title": "ページ全体の初回設定",
        "page_setup": (
            "ページ全体の撮影には、初回だけ拡張機能の読み込みが必要です。\n"
            "ブラウザは終了も再起動もしません。\n\n"
            "1. QuickShot を起動したまま、Chrome または Edge で拡張機能の管理を開く\n"
            "2. デベロッパーモードをオンにする\n"
            "3. 「パッケージ化されていない拡張機能を読み込む」で次のフォルダを選ぶ\n"
            "{folder}\n"
            "4. すでに読み込んでいる場合は、その拡張機能を再読み込みする\n"
            "5. 撮影したい http(s) のページを表示し、パネルの「ページ」を押す\n\n"
            "chrome:// のページや、拡張機能が未接続のときは撮影できません。"
        ),
        "page_disconnected": "QuickShot との接続がまだありません。QuickShot を起動してから拡張機能を読み込み直してください。",
        "page_no_tab": "表示中のページが見つかりません。",
        "page_need_http": "Chrome または Edge で http または https のページを開いてください。",
        "page_no_size": "ページのサイズを取得できませんでした。",
        "page_handoff": "画像の受け渡しに失敗しました。",
        "page_progress": "撮影中 {n}",
        "always_top": "常に最前面",
        "copy_image": "撮影後にコピー",
        "copy_button": "クリップボードへコピー",
        "history": "履歴",
        "ocr": "文字認識",
        "edit": "編集",
        "hotkey_failed": "Ctrl+Shift+1、2、3 のショートカットを登録できませんでした。ほかのアプリが使っています。",
        "ocr_failed": "文字認識に失敗しました",
        "ocr_missing": "Windows の文字認識言語が入っていません",
        "ocr_working": "文字を認識しています",
        "copy_text": "全文をコピー",
        "save_text": "テキストを保存",
        "undo": "元に戻す",
        "save_as": "別名で保存",
        "crop": "切り抜き",
        "rect": "四角",
        "arrow": "矢印",
        "text": "文字",
        "mosaic": "モザイク",
        "edit_saved": "編集した画像を保存しました",
        "edit_large": "画像が大きすぎて編集できません",
        "edit_keep": "元の画像は上書きしません。別の名前で保存してください",
        "edit_hint": "切り抜きかモザイクを選び、画像の上をドラッグします。元の画像は上書きしません。",
        "chat_capture": "ChatGPT会話撮影",
        "chat_capture_off": "ChatGPT会話撮影（ChatGPTのページでのみ）",
        "chat_saved": "ChatGPTの会話を保存しました",
        "chat_not_found": "会話本文の領域を特定できませんでした。通常のページ全体撮影は使えます。",
        "history_missing": "ファイルが見つかりません",
        "history_forget": "履歴から削除",
        "history_delete": "画像ファイルを削除",
        "history_confirm": "この画像ファイルを削除しますか？",
        "open_image": "画像を開く",
        "no_history": "履歴はありません",
        "area_saved": "範囲を保存しました",
        "chat_need_page": "ChatGPTのページを前面にしてから、もう一度選んでください",
    },
    "en": {
        "exit": "Exit",
        "copied": "Copied",
        "failed": "Copy failed",
        "tip": "Drag to move",
        "select": "Select an area and capture",
        "select_short": "Area",
        "screen_short": "Screen",
        "page_short": "Page",
        "settings": "Settings",
        "choose_folder": "Choose folder",
        "open_folder": "Open folder",
        "save_folder": "Save folder",
        "close": "Close",
        "folder_failed": "Could not open the folder",
        "already": "QuickShot is already running.",
        "screen": "Save entire screen",
        "page": "Save entire page",
        "saved_one": "Saved the entire screen",
        "saved_many": "Saved {n} monitors as one image",
        "screen_failed": "Could not save the entire screen",
        "screen_large": "The desktop is too large to save as one image",
        "page_checking": "Checking the connection",
        "page_start": "Capturing the page from the top",
        "page_saved": "Saved the entire page",
        "page_truncated": "The page was long, so only the top portion was saved",
        "page_parts": "Saved the whole page as {n} images",
        "chat_parts": "Saved the ChatGPT conversation as {n} images",
        "page_parts_partial": "Saved {n} images. The rest was not saved.",
        "parts_no_copy": "Multiple images were not copied to the clipboard.",
        "page_too_wide": "The page is too wide to save",
        "page_partial_top": "Older content was still loading, so only the loaded range was saved",
        "page_partial_bottom": "The capture stopped before the bottom, so this image is incomplete",
        "page_failed": "Could not capture the entire page",
        "page_timeout": "The page capture did not finish",
        "page_no_response": "The extension did not respond. Keep QuickShot running and reload the extension.",
        "page_permission": "Full-page capture does not have the required permission. Reload QuickShot Page Capture, and set site access to all sites.",
        "page_capture_timeout": "The browser stopped responding while capturing, so the attempt was cancelled. Bring the page to the front and try again.",
        "cancel": "Cancel",
        "page_setup_title": "One-time page capture setup",
        "page_setup": (
            "Full-page capture needs the extension loaded once.\n"
            "QuickShot does not close or restart the browser.\n\n"
            "1. Keep QuickShot running and open the extensions page in Chrome or Edge\n"
            "2. Turn on Developer mode\n"
            "3. Choose Load unpacked and select this folder\n"
            "{folder}\n"
            "4. If it is already loaded, reload that extension\n"
            "5. Open the http(s) page and press Page on the panel\n\n"
            "chrome:// pages cannot be captured, and capture fails until the extension is connected."
        ),
        "page_disconnected": "QuickShot is not connected yet. Start QuickShot, then reload the extension.",
        "page_no_tab": "No visible page was found.",
        "page_need_http": "Open an http or https page in Chrome or Edge.",
        "page_no_size": "Could not read the page size.",
        "page_handoff": "Could not hand the image back to QuickShot.",
        "page_progress": "Capturing {n}",
        "always_top": "Always on top",
        "copy_image": "Copy after capture",
        "copy_button": "Copy to clipboard",
        "history": "History",
        "ocr": "Text recognition",
        "edit": "Edit",
        "hotkey_failed": "Could not register Ctrl+Shift+1, 2, and 3. Another app is using them.",
        "ocr_failed": "Text recognition failed",
        "ocr_missing": "Windows OCR languages are not installed",
        "ocr_working": "Recognizing text",
        "copy_text": "Copy all text",
        "save_text": "Save text",
        "undo": "Undo",
        "save_as": "Save as",
        "crop": "Crop",
        "rect": "Rectangle",
        "arrow": "Arrow",
        "text": "Text",
        "mosaic": "Mosaic",
        "edit_saved": "Saved the edited image",
        "edit_large": "The image is too large to edit",
        "edit_keep": "The original image is kept. Save it under another name",
        "edit_hint": "Choose Crop or Mosaic, then drag on the image. The original file is not overwritten.",
        "chat_capture": "Capture ChatGPT conversation",
        "chat_capture_off": "Capture ChatGPT conversation (ChatGPT pages only)",
        "chat_saved": "Saved the ChatGPT conversation",
        "chat_not_found": "The conversation area was not found. Full-page capture is still available.",
        "history_missing": "The file is missing",
        "history_forget": "Remove from history",
        "history_delete": "Delete the image file",
        "history_confirm": "Delete this image file?",
        "open_image": "Open image",
        "no_history": "No captures yet",
        "area_saved": "Saved the selected area",
        "chat_need_page": "Bring a ChatGPT page to the front, then try again",
    },
}

EXTENSION_TEXT = {
    "ページ全体の撮影に失敗しました": "page_failed",
    "QuickShot との接続がまだありません。QuickShot を起動してから拡張機能を読み込み直してください。": "page_disconnected",
    "表示中のページが見つかりません。": "page_no_tab",
    "Chrome または Edge で http または https のページを開いてください。": "page_need_http",
    "ページのサイズを取得できませんでした。": "page_no_size",
    "画像の受け渡しに失敗しました。": "page_handoff",
    "Either the '<all_urls>' or 'activeTab' permission is required.": "page_permission",
    "This request exceeds the MAX_CAPTURE_VISIBLE_TAB_CALLS_PER_SECOND quota.": "page_capture_timeout",
    "capture-timeout": "page_capture_timeout",
    "ChatGPTのページを前面にしてから、もう一度選んでください。": "chat_need_page",
    "会話本文の領域を特定できませんでした。通常のページ全体撮影は使えます。": "chat_not_found",
    "画面が広すぎて1枚に保存できません": "page_too_wide",
}


def settings_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "OKAWARI", "QuickShot")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def button_size(dpi):
    return max(48, int(round(52 * (dpi or 96) / 96)))


def panel_width(dpi):
    return button_size(dpi)


def panel_footer(dpi):
    return max(22, int(round(22 * (dpi or 96) / 96)))


def panel_height(dpi):
    return button_size(dpi) * 3 + panel_footer(dpi)


def monitor_for_point(x, y, mons):
    for mon in mons:
        if mon[0] <= x < mon[2] and mon[1] <= y < mon[3]:
            return mon
    return min(
        mons,
        key=lambda mon: (max(mon[0], min(x, mon[2])) - x) ** 2
        + (max(mon[1], min(y, mon[3])) - y) ** 2,
    )


def clamp_button(x, y, size, mons, height=None):
    span_h = size if height is None else height
    mon = monitor_for_point(x + size / 2, y + span_h / 2, mons)
    left, top, right, bottom = mon[5], mon[6], mon[7], mon[8]
    if right - left < size or bottom - top < span_h:
        left, top, right, bottom = mon[0], mon[1], mon[2], mon[3]
    nx = min(max(int(x), left), max(left, right - size))
    ny = min(max(int(y), top), max(top, bottom - span_h))
    return nx, ny, mon[4]


def default_button_origin():
    mons = capture.monitors()
    primary = next((mon for mon in mons if mon[0] <= 0 < mon[2] and mon[1] <= 0 < mon[3]), mons[0])
    left, top, right, bottom, dpi = primary[0], primary[1], primary[2], primary[3], primary[4]
    width = panel_width(dpi)
    height = panel_height(dpi)
    x = right - width - 16
    y = top + max(0, (bottom - top - height) // 2)
    x, y, dpi = clamp_button(x, y, width, mons, height)
    return x, y, dpi


def clamp_rect(x, y, width, height):
    vx, vy, vw, vh = capture.virtual_screen()
    x2 = min(x + width, vx + vw)
    y2 = min(y + height, vy + vh)
    x = max(x, vx)
    y = max(y, vy)
    return int(x), int(y), int(x2 - x), int(y2 - y)


def localize_extension_text(lang, text):
    catalog = STRINGS.get(lang, STRINGS["en"])
    key = EXTENSION_TEXT.get(text)
    if key:
        return catalog[key]
    prefix = "撮影中 "
    if isinstance(text, str) and text.startswith(prefix):
        return catalog["page_progress"].format(n=text[len(prefix):])
    return text


def finish_menu(root, menu, choice):
    """Let a deferred menu command run, then destroy the menu.

    On Windows, Tk runs the selected command after tk_popup returns.
    Destroying the menu first drops that command, so flush events while
    the menu still exists.
    """
    try:
        root.update()
    except tk.TclError:
        pass
    try:
        menu.unpost()
    except tk.TclError:
        pass
    try:
        menu.destroy()
    except tk.TclError:
        pass
    return choice.get("action")


def process_note():
    args = " ".join(sys.argv)[:240]
    return "pid=%s ppid=%s argv=%s" % (os.getpid(), os.getppid(), args)


def app_log(text):
    try:
        path = os.path.join(os.path.dirname(settings_path()), "quickshot.log")
        line = time.strftime("%Y-%m-%d %H:%M:%S ") + str(text).replace("\r", " ").replace("\n", " | ")[:1000]
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except Exception:
        return


def peek_lang():
    try:
        with open(settings_path(), encoding="utf-8") as handle:
            lang = json.load(handle).get("lang")
        if lang in STRINGS:
            return lang
    except Exception:
        pass
    return capture.windows_ui_lang()


class App:
    def __init__(self):
        self.lang = peek_lang()
        self.busy = False
        self.closing = False
        self.size = 78
        self.width = 78
        self.row = 26
        self.save_dir = ""
        self.settings = None
        self.result = None
        self.result_folder = ""
        self.press_row = None
        self.press = None
        self.origin = None
        self.moved = False
        self.sel_start = None
        self.rect_id = None
        self.overlay = None
        self.canvas = None
        self.tip = None
        self.tip_job = None
        self.toast = None
        self.toast_job = None
        self.page_job = None
        self.page_started = 0
        self.page_waiting = False
        self.page_phase = ""
        self.page_mode = "page"
        self.page_text = ""
        self.chat_page = False
        self.result_waiting = False
        self.bridge = None
        self.setup = None
        self.setup_label = None
        self.menu_open = False
        self.always_top = True
        self.copy_images = True
        self._panel_concealed = False
        self._hot_at = 0.0
        self._hotkey = None
        self.result_path = ""
        self.history_window = None
        self.ocr_window = None
        self.editor_window = None
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("QuickShotResident")
        try:
            self.root.attributes("-alpha", 1.0)
        except tk.TclError:
            pass
        self.win = tk.Toplevel(self.root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="#1d4ed8", cursor="hand2")
        self.icon = tk.Canvas(
            self.win, bg="#1d4ed8", highlightthickness=0, borderwidth=0, cursor="hand2"
        )
        self.icon.pack(fill="both", expand=True)
        self.icon.bind("<ButtonPress-1>", self.on_press)
        self.icon.bind("<B1-Motion>", self.on_motion)
        self.icon.bind("<ButtonRelease-1>", self.on_release)
        self.icon.bind("<Button-3>", self.on_right_click)
        self.icon.bind("<Enter>", self.schedule_tip)
        self.icon.bind("<Leave>", lambda _event: self.hide_tip())
        self.place_initial()
        self.win.deiconify()
        self.win.lift()
        self.win.attributes("-topmost", True)
        self.root.update()
        app_log(
            "gui start %s %s icon %s,%s %sx%s"
            % (VERSION, process_note(), self.pos[0], self.pos[1], self.size, self.height)
        )
        if capture.tray_add(int(self.win.winfo_id())):
            app_log("tray add")
        else:
            app_log("tray add failed")
        self.root.report_callback_exception = self._tk_error
        try:
            self.bridge = bridge.Bridge()
            self.extension_dir = self.bridge.start()
        except Exception:
            app_log(traceback.format_exc())
            self.bridge = None
            self.extension_dir = ""
        try:
            import hotkey
            self._hotkey = hotkey
            if hotkey.register():
                self.root.after(800, lambda: self.show_notice(self.tr("hotkey_failed")))
        except Exception:
            app_log(traceback.format_exc())
            self._hotkey = None
        self.root.after(200, self.poll_hotkeys)
        self.root.after(1200, self.keep_top)

    def _tk_error(self, etype, value, tb):
        app_log("tk error " + "".join(traceback.format_exception(etype, value, tb))[:800])

    def tr(self, key):
        return STRINGS.get(self.lang, STRINGS["en"]).get(key, key)

    def place_initial(self):
        saved_x = None
        saved_y = None
        try:
            with open(settings_path(), encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                saved_x = data.get("x")
                saved_y = data.get("y")
                if data.get("lang") in STRINGS:
                    self.lang = data["lang"]
                if "top" in data:
                    self.always_top = bool(data.get("top"))
                if "copy" in data:
                    self.copy_images = bool(data.get("copy"))
                folder = data.get("dir")
                if isinstance(folder, str) and pngsave.set_output_dir(folder):
                    self.save_dir = pngsave.output_dir()
        except Exception:
            pass
        if isinstance(saved_x, (int, float)) and isinstance(saved_y, (int, float)):
            mons = capture.monitors()
            dpi = monitor_for_point(saved_x, saved_y, mons)[4]
            x, y, dpi = clamp_button(saved_x, saved_y, panel_width(dpi), mons, panel_height(dpi))
            self.apply_geometry(x, y, dpi)
        else:
            x, y, dpi = default_button_origin()
            self.apply_geometry(x, y, dpi)
        self.apply_topmost()

    def apply_geometry(self, x, y, dpi):
        self.size = button_size(dpi)
        self.width = self.size
        self.footer = panel_footer(dpi)
        self.height = self.size * 3 + self.footer
        self.pos = (int(x), int(y))
        self.icon.configure(width=self.width, height=self.height)
        self.win.geometry(f"{self.width}x{self.height}+{self.pos[0]}+{self.pos[1]}")
        self.draw_icon()

    def row_at(self, y, x=None):
        if y is None or y < 0 or y >= self.height:
            return None
        if y < self.size * 3:
            return min(2, int(y // self.size))
        if x is None or x < 0 or x >= self.width:
            return None
        return 3 + min(2, int(x * 3 / self.width))

    def row_label(self, key):
        if key == "lang":
            return "EN" if self.lang == "ja" else "あ"
        if key == "settings":
            return self.tr("settings")
        if key == "exit":
            return self.tr("exit")
        return self.tr(key + "_short")

    def draw_icon(self):
        size = self.size
        canvas = self.icon
        canvas.delete("all")
        colors = ("#1d4ed8", "#1e40af", "#1e3a8a")
        for index, color in enumerate(colors):
            top = index * size
            canvas.create_rectangle(0, top, size, top + size, fill=color, outline="")
        canvas.create_rectangle(size * 0.22, size * 0.40, size * 0.78, size * 0.72, fill="white", outline="")
        canvas.create_polygon(
            size * 0.36, size * 0.40,
            size * 0.44, size * 0.28,
            size * 0.62, size * 0.28,
            size * 0.70, size * 0.40,
            fill="white", outline="",
        )
        canvas.create_oval(size * 0.40, size * 0.46, size * 0.60, size * 0.66, fill="#1d4ed8", outline="")
        canvas.create_rectangle(size * 0.22, size + size * 0.22, size * 0.78, size + size * 0.78, outline="white", width=2)
        canvas.create_line(size * 0.28, size * 2 + size * 0.34, size * 0.72, size * 2 + size * 0.34, fill="white", width=2)
        canvas.create_line(size * 0.28, size * 2 + size * 0.50, size * 0.72, size * 2 + size * 0.50, fill="white", width=2)
        canvas.create_line(size * 0.28, size * 2 + size * 0.66, size * 0.56, size * 2 + size * 0.66, fill="white", width=2)
        top = size * 3
        canvas.create_rectangle(0, top, size, self.height, fill="#172554", outline="")
        cell = size / 3
        mid = top + (self.height - top) / 2
        cx = cell * 0.5
        canvas.create_oval(cx - 5, mid - 5, cx + 5, mid + 5, outline="white", width=1)
        canvas.create_oval(cx - 1.5, mid - 1.5, cx + 1.5, mid + 1.5, fill="white", outline="")
        canvas.create_text(cell * 1.5, mid, text=self.row_label("lang"), fill="white", font=("Segoe UI", 8))
        cx = cell * 2.5
        canvas.create_line(cx - 4, mid - 4, cx + 4, mid + 4, fill="white", width=1)
        canvas.create_line(cx + 4, mid - 4, cx - 4, mid + 4, fill="white", width=1)

    def run_panel(self, row):
        key = PANEL[row]
        if key == "select":
            self.begin_select()
        elif key == "screen":
            self.capture_screen()
        elif key == "page":
            self.capture_page()
        elif key == "settings":
            self.show_settings()
        elif key == "lang":
            self.set_lang("en" if self.lang == "ja" else "ja")
        elif key == "exit":
            self.quit()

    def save_settings(self):
        try:
            payload = {"x": self.pos[0], "y": self.pos[1], "lang": self.lang}
            if getattr(self, "save_dir", ""):
                payload["dir"] = self.save_dir
            payload["top"] = bool(getattr(self, "always_top", True))
            payload["copy"] = bool(getattr(self, "copy_images", True))
            path = settings_path()
            temp = path + ".tmp"
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            os.replace(temp, path)
        except Exception:
            return

    def set_lang(self, lang, reopen=None):
        if lang not in STRINGS:
            return
        changed = lang != self.lang
        self.lang = lang
        self.save_settings()
        self.hide_tip()
        self.draw_icon()
        self.refresh_setup()
        self.refresh_settings()
        self.refresh_result_buttons()
        editor = getattr(self, "editor_window", None)
        if editor is not None:
            try:
                editor.refresh_labels()
            except tk.TclError:
                self.editor_window = None
        if changed and reopen is not None:
            px, py = int(reopen[0]), int(reopen[1])
            self.root.after_idle(lambda px=px, py=py: self.show_menu(px, py))

    def on_press(self, event):
        if self.busy:
            return "break"
        self.hide_tip()
        self.press = (event.x_root, event.y_root)
        self.origin = (self.win.winfo_x(), self.win.winfo_y())
        self.moved = False
        self.press_row = self.row_at(event.y, event.x)
        try:
            self.win.grab_set()
        except tk.TclError:
            pass
        return "break"

    def on_motion(self, event):
        if not self.press or not self.origin or self.busy:
            return "break"
        dx = event.x_root - self.press[0]
        dy = event.y_root - self.press[1]
        if abs(dx) + abs(dy) > 6:
            self.moved = True
        self.win.geometry(f"+{int(self.origin[0] + dx)}+{int(self.origin[1] + dy)}")
        return "break"

    def on_release(self, event):
        try:
            self.win.grab_release()
        except tk.TclError:
            pass
        if self.busy or not self.press or not self.origin:
            self.press = None
            self.origin = None
            self.moved = False
            self.press_row = None
            return "break"
        dx = event.x_root - self.press[0]
        dy = event.y_root - self.press[1]
        moved = self.moved
        origin = self.origin
        row = self.press_row
        self.press = None
        self.origin = None
        self.moved = False
        self.press_row = None
        if moved:
            mons = capture.monitors()
            drop_x = origin[0] + dx
            drop_y = origin[1] + dy
            dpi = monitor_for_point(drop_x + self.width / 2, drop_y + self.height / 2, mons)[4]
            x, y, dpi = clamp_button(drop_x, drop_y, panel_width(dpi), mons, panel_height(dpi))
            self.apply_geometry(x, y, dpi)
            self.save_settings()
        elif row is not None and self.row_at(event.y, event.x) == row:
            self.run_panel(row)
        return "break"

    def on_right_click(self, event):
        self.show_menu(event.x_root, event.y_root)
        return "break"

    def show_menu(self, x, y):
        if self.busy or self.menu_open:
            return
        self.refresh_chat_menu()
        self.menu_open = True
        self.hide_tip()
        try:
            self.win.grab_release()
        except tk.TclError:
            pass
        menu = tk.Menu(self.win, tearoff=0)
        choice = {}

        def choose(action):
            choice["action"] = action

        menu.add_command(label=self.tr("select"), command=lambda: choose("select"))
        menu.add_command(label=self.tr("screen"), command=lambda: choose("screen"))
        menu.add_command(label=self.tr("page"), command=lambda: choose("page"))
        if self.chat_page:
            menu.add_command(label=self.tr("chat_capture"), command=lambda: choose("chat"))
        else:
            menu.add_command(label=self.tr("chat_capture_off"), state="disabled")
        menu.add_command(label=self.tr("history"), command=lambda: choose("history"))
        menu.add_command(label=self.tr("ocr"), command=lambda: choose("ocr"))
        menu.add_command(label=self.tr("edit"), command=lambda: choose("edit"))
        menu.add_separator()
        menu.add_command(
            label="日本語 ✓" if self.lang == "ja" else "日本語",
            command=lambda: choose("ja"),
        )
        menu.add_command(
            label="English ✓" if self.lang == "en" else "English",
            command=lambda: choose("en"),
        )
        menu.add_separator()
        menu.add_command(label=self.tr("exit"), command=lambda: choose("exit"))
        action = None
        try:
            menu.tk_popup(int(x), int(y))
            action = finish_menu(self.root, menu, choice)
        except tk.TclError:
            app_log("chat menu create failed")
            action = None
        finally:
            self.menu_open = False
            if action is None:
                try:
                    menu.destroy()
                except tk.TclError:
                    pass
        self.run_menu_action(action, int(x), int(y))

    def run_menu_action(self, action, x, y):
        if action == "select":
            self.begin_select()
        elif action == "screen":
            self.capture_screen()
        elif action == "page":
            self.capture_page()
        elif action == "chat":
            app_log("chat menu click")
            self.capture_page("chat")
        elif action == "history":
            self.show_history()
        elif action == "ocr":
            self.show_ocr()
        elif action == "edit":
            self.show_editor()
        elif action in ("ja", "en"):
            self.set_lang(action, reopen=(x, y))
        elif action == "exit":
            self.quit()

    def schedule_tip(self, _event=None):
        self.hide_tip()
        if not self.busy:
            self.tip_job = self.root.after(600, self.show_tip)

    def show_tip(self):
        self.tip_job = None
        if self.busy:
            return
        tip = tk.Toplevel(self.root)
        tip.withdraw()
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg="#16181d")
        tk.Label(
            tip, text=self.tr("tip"), bg="#16181d", fg="white",
            font=("Segoe UI", 9), padx=8, pady=4,
        ).pack()
        tip.update_idletasks()
        x = self.win.winfo_x()
        y = self.win.winfo_y() + self.height + 6
        tip.geometry(f"+{int(x)}+{int(y)}")
        tip.deiconify()
        self.tip = tip

    def hide_tip(self):
        if self.tip_job is not None:
            try:
                self.root.after_cancel(self.tip_job)
            except tk.TclError:
                pass
            self.tip_job = None
        if self.tip is not None:
            try:
                self.tip.destroy()
            except tk.TclError:
                pass
            self.tip = None

    def close_toast(self):
        if self.toast_job is not None:
            try:
                self.root.after_cancel(self.toast_job)
            except tk.TclError:
                pass
            self.toast_job = None
        if self.toast is not None:
            try:
                self.toast.destroy()
            except tk.TclError:
                pass
            self.toast = None

    def show_toast(self, key):
        self.show_notice(self.tr(key), 1200)

    def make_opaque(self, window):
        # Do not set -alpha here. On this PC, setting it while the window is
        # withdrawn makes the whole dialog, including its title bar, show the
        # page underneath even when the value is 1.0.
        try:
            window.attributes("-topmost", True)
            window.lift()
        except tk.TclError:
            pass

    def show_result(self, text, folder=None, waiting=False, file=None):
        self.result_folder = folder or ""
        self.result_waiting = waiting
        if not waiting:
            self.result_path = file or ""
        if self.result is not None:
            try:
                if self.result.winfo_exists():
                    self.result_label.configure(text=text)
                    self.refresh_result_buttons()
                    self.place_result()
                    self.result.lift()
                    self.make_opaque(self.result)
                    self.result.deiconify()
                    return
            except tk.TclError:
                self.result = None
        window = tk.Toplevel(self.root)
        window.withdraw()
        window.title("QuickShot")
        window.configure(bg="#16181d")
        window.attributes("-topmost", True)
        window.resizable(False, False)
        self.make_opaque(window)
        self.result_label = tk.Label(
            window, text=text, bg="#16181d", fg="white", justify="left",
            wraplength=340, font=("Segoe UI", 10), padx=14, pady=12,
        )
        self.result_label.pack(anchor="w")
        bar = tk.Frame(window, bg="#16181d")
        bar.pack(anchor="e", padx=12, pady=(0, 12))
        button_style = {
            "bg": "#f3f4f6",
            "fg": "#111827",
            "activebackground": "#e5e7eb",
            "activeforeground": "#111827",
        }
        self.result_open = tk.Button(bar, command=self.open_result_folder, **button_style)
        self.result_ocr = tk.Button(bar, command=self.open_result_ocr, **button_style)
        self.result_edit = tk.Button(bar, command=self.open_result_edit, **button_style)
        self.result_cancel = tk.Button(bar, command=self.close_result, **button_style)
        self.result_close = tk.Button(bar, command=self.close_result, **button_style)
        self.result_open.pack(side="left", padx=(0, 8))
        self.result_cancel.pack(side="left", padx=(0, 8))
        self.result_close.pack(side="left")
        self.result = window
        window.protocol("WM_DELETE_WINDOW", self.close_result)
        self.refresh_result_buttons()
        self.place_result()
        window.deiconify()
        self.make_opaque(window)

    def refresh_result_buttons(self):
        if self.result is None:
            return
        try:
            self.result_close.configure(text=self.tr("close"))
            self.result_cancel.configure(text=self.tr("cancel"))
            self.result_ocr.configure(text=self.tr("ocr"))
            self.result_edit.configure(text=self.tr("edit"))
            if self.result_waiting:
                self.result_open.pack_forget()
                self.result_ocr.pack_forget()
                self.result_edit.pack_forget()
                self.result_close.pack_forget()
                self.result_cancel.pack(side="left")
            else:
                self.result_cancel.pack_forget()
                self.result_close.pack(side="left")
                if self.result_path:
                    self.result_ocr.pack(side="left", padx=(0, 8), before=self.result_close)
                    self.result_edit.pack(side="left", padx=(0, 8), before=self.result_close)
                else:
                    self.result_ocr.pack_forget()
                    self.result_edit.pack_forget()
                if self.result_folder:
                    self.result_open.configure(text=self.tr("open_folder"))
                    self.result_open.pack(side="left", padx=(0, 8), before=self.result_close)
                else:
                    self.result_open.pack_forget()
        except tk.TclError:
            self.result = None

    def place_result(self):
        if self.result is None:
            return
        self.result.update_idletasks()
        width = self.result.winfo_reqwidth()
        x = self.win.winfo_x() - width - 8
        y = self.win.winfo_y()
        if x < capture.virtual_screen()[0]:
            x = self.win.winfo_x() + self.width + 8
        self.result.geometry(f"+{int(x)}+{int(y)}")

    def open_result_folder(self):
        folder = self.result_folder or pngsave.output_dir()
        try:
            os.startfile(folder)
        except Exception:
            app_log(traceback.format_exc())
            self.show_result(self.tr("folder_failed"))

    def close_result(self):
        if self.page_waiting:
            app_log("page cancel")
            self.stop_page_wait()
        if self.result is not None:
            try:
                self.result.destroy()
            except tk.TclError:
                pass
            self.result = None
            self.result_folder = ""

    def lift_dialogs(self):
        for window in (self.result, self.setup):
            if window is None:
                continue
            try:
                if window.winfo_exists():
                    window.attributes("-topmost", True)
                    window.lift()
            except tk.TclError:
                pass

    def show_notice(self, text, ms=6000):
        self.close_toast()
        toast = tk.Toplevel(self.root)
        toast.withdraw()
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg="#16181d")
        tk.Label(
            toast, text=text, bg="#16181d", fg="white",
            font=("Segoe UI", 10), padx=12, pady=8, wraplength=360, justify="left",
        ).pack()
        toast.update_idletasks()
        height = toast.winfo_reqheight()
        x = self.win.winfo_x()
        y = self.win.winfo_y() - height - 8
        if y < capture.virtual_screen()[1]:
            y = self.win.winfo_y() + self.height + 8
        toast.geometry(f"+{int(x)}+{int(y)}")
        self.make_opaque(toast)
        toast.deiconify()
        self.make_opaque(toast)
        capture.exclude_window_from_capture(int(toast.winfo_id()))
        self.toast = toast
        self.toast_job = self.root.after(ms, self.close_toast)

    def _quickshot_windows(self):
        return (
            getattr(self, "win", None),
            getattr(self, "result", None),
            getattr(self, "settings", None),
            getattr(self, "setup", None),
            getattr(self, "ocr_window", None),
            getattr(self, "editor_window", None),
            getattr(self, "history_window", None),
        )

    def hide_for_shot(self):
        """Withdraw QuickShot windows that are actually visible. Remember them."""
        hidden = []
        for window in self._quickshot_windows():
            if window is None:
                continue
            try:
                if window.winfo_exists() and window.winfo_viewable():
                    hidden.append(window)
                    window.withdraw()
            except tk.TclError:
                continue
        self.close_toast()
        self.hide_tip()
        panel = getattr(self, "win", None)
        if panel in hidden and not self._panel_concealed:
            self._panel_concealed = True
            app_log("panel hide")
        self._shot_hidden = hidden
        self.root.update()
        self.pump(0.16)

    def restore_after_shot(self):
        hidden = list(getattr(self, "_shot_hidden", []) or [])
        self._shot_hidden = []
        panel = getattr(self, "win", None)
        for window in hidden:
            if window is panel:
                continue
            try:
                if window.winfo_exists():
                    window.deiconify()
            except tk.TclError:
                continue
        if panel in hidden and not self.closing:
            self._panel_concealed = True
            self.reveal_panel()
        elif not self._panel_concealed and not self.closing:
            self.reveal_panel()

    def capture_screen(self):
        if self.busy or self.closing:
            return
        if self.page_waiting:
            app_log("page cancel")
            self.stop_page_wait()
        self.busy = True
        path = None
        error = None
        count = 1
        try:
            self.hide_for_shot()
            if self.win.winfo_viewable():
                app_log("panel still visible")
                self.pump(0.12)
            path, count, _width, _height = pngsave.save_full_screen()
            app_log("screen saved " + path)
        except ValueError:
            app_log(traceback.format_exc())
            error = "screen_large"
        except Exception:
            app_log(traceback.format_exc())
            error = "screen_failed"
        finally:
            self.restore_after_shot()
            self.busy = False
        if error:
            self.show_result(self.tr(error))
        elif path:
            self.note_capture(path)
            label = self.tr("saved_one") if count <= 1 else self.tr("saved_many").format(n=count)
            self.show_result(label + "\n" + path, os.path.dirname(path), file=path)

    def show_settings(self):
        if self.settings is not None:
            try:
                if self.settings.winfo_exists():
                    self.refresh_settings()
                    self.settings.lift()
                    return
            except tk.TclError:
                pass
            self.settings = None
        window = tk.Toplevel(self.root)
        window.title(self.tr("settings"))
        window.configure(bg="white")
        window.geometry("460x300")
        window.attributes("-topmost", True)
        self.make_opaque(window)
        window.resizable(False, False)
        self.settings_heading = tk.Label(window, bg="white", fg="#111827", font=("Segoe UI", 10))
        self.settings_heading.pack(anchor="w", padx=16, pady=(12, 4))
        self.settings_path_label = tk.Label(
            window, bg="white", fg="#374151", justify="left", wraplength=400, font=("Segoe UI", 9)
        )
        self.settings_path_label.pack(anchor="w", padx=16, pady=(0, 10))
        buttons = tk.Frame(window, bg="white")
        buttons.pack(anchor="w", padx=16)
        self.settings_choose = tk.Button(buttons, command=self.choose_folder)
        self.settings_choose.pack(side="left", padx=(0, 8))
        self.settings_open = tk.Button(buttons, command=self.open_save_folder)
        self.settings_open.pack(side="left", padx=(0, 8))
        self.settings_close = tk.Button(buttons, command=self.close_settings)
        self.settings_close.pack(side="left")
        options = tk.Frame(window, bg="white")
        options.pack(anchor="w", padx=16, pady=(12, 0))
        self.top_var = tk.BooleanVar(value=self.always_top)
        self.copy_var = tk.BooleanVar(value=self.copy_images)
        self.top_check = tk.Checkbutton(
            options, variable=self.top_var, command=self.on_top_toggle,
            bg="white", anchor="w",
        )
        self.top_check.pack(anchor="w")
        self.copy_check = tk.Checkbutton(
            options, variable=self.copy_var, command=self.on_copy_toggle,
            bg="white", anchor="w",
        )
        self.copy_check.pack(anchor="w")
        tools = tk.Frame(window, bg="white")
        tools.pack(anchor="w", padx=16, pady=(8, 0))
        self.history_button = tk.Button(tools, command=self.show_history)
        self.history_button.pack(side="left", padx=(0, 8))
        self.ocr_button = tk.Button(tools, command=self.show_ocr)
        self.ocr_button.pack(side="left", padx=(0, 8))
        self.edit_button = tk.Button(tools, command=self.show_editor)
        self.edit_button.pack(side="left")
        self.settings = window
        window.protocol("WM_DELETE_WINDOW", self.close_settings)
        self.refresh_settings()

    def refresh_settings(self):
        if self.settings is None:
            return
        try:
            if not self.settings.winfo_exists():
                self.settings = None
                return
            self.settings.title(self.tr("settings"))
            self.settings_heading.configure(text=self.tr("save_folder"))
            self.settings_path_label.configure(text=pngsave.output_dir())
            self.settings_choose.configure(text=self.tr("choose_folder"))
            self.settings_open.configure(text=self.tr("open_folder"))
            self.settings_close.configure(text=self.tr("close"))
            self.top_check.configure(text=self.tr("always_top"))
            self.copy_check.configure(text=self.tr("copy_image"))
            self.top_var.set(self.always_top)
            self.copy_var.set(self.copy_images)
            self.history_button.configure(text=self.tr("history"))
            self.ocr_button.configure(text=self.tr("ocr"))
            self.edit_button.configure(text=self.tr("edit"))
        except tk.TclError:
            self.settings = None

    def choose_folder(self):
        if self.settings is None:
            return
        chosen = filedialog.askdirectory(
            parent=self.settings,
            initialdir=pngsave.output_dir(),
            title=self.tr("choose_folder"),
            mustexist=True,
        )
        if not chosen:
            return
        if not pngsave.set_output_dir(chosen):
            self.show_notice(self.tr("folder_failed"))
            return
        self.save_dir = pngsave.output_dir()
        self.save_settings()
        self.refresh_settings()

    def open_save_folder(self):
        folder = pngsave.output_dir()
        try:
            os.startfile(folder)
        except Exception:
            app_log(traceback.format_exc())
            self.show_notice(self.tr("folder_failed"))

    def close_settings(self):
        if self.settings is not None:
            try:
                self.settings.destroy()
            except tk.TclError:
                pass
            self.settings = None

    def on_top_toggle(self):
        self.always_top = bool(self.top_var.get())
        self.save_settings()
        self.apply_topmost()

    def on_copy_toggle(self):
        self.copy_images = bool(self.copy_var.get())
        self.save_settings()

    def discard_page_messages(self):
        if self.bridge is None:
            return
        try:
            for message in self.bridge.take_messages():
                kind = message.get("type")
                if kind == "tab":
                    self.apply_tab_message(message)
                elif kind == "diag":
                    self.apply_diag(message)
        except Exception:
            app_log(traceback.format_exc())

    def stop_page_wait(self):
        self.page_waiting = False
        self.page_phase = ""
        if self.page_job is not None:
            try:
                self.root.after_cancel(self.page_job)
            except tk.TclError:
                pass
            self.page_job = None
        self.discard_page_messages()
        reveal = getattr(self, "reveal_panel", None)
        if callable(reveal):
            reveal()

    def _log_menu_gap(self, text):
        now = time.time()
        if now - getattr(self, "_menu_gap_log", 0) < 30:
            return
        self._menu_gap_log = now
        app_log(text)

    def _note_extension(self, version):
        if not isinstance(version, str) or len(version) > 16:
            return
        if any(char not in "0123456789." for char in version):
            return
        if version and version != getattr(self, "ext_version", ""):
            self.ext_version = version
            app_log("extension " + version)

    def _log_chat_menu(self, enabled, host, path, reason):
        signature = ("on", host, path) if enabled else ("off", "", "")
        if signature == getattr(self, "_tab_signature", None):
            return
        self._tab_signature = signature
        if enabled:
            app_log("chat menu on host %s path %s %s" % (host or "-", path or "-", reason or "-"))
        else:
            app_log("chat menu off host %s path %s %s" % (host or "-", path or "-", reason or "-"))

    def apply_diag(self, message):
        if not isinstance(message, dict):
            return
        event = message.get("event")
        if event == "host-connected":
            version = message.get("version") if isinstance(message.get("version"), str) else ""
            now = time.time()
            if version != getattr(self, "ext_version", "") or now - getattr(self, "_ext_log", 0) > 60:
                self._ext_log = now
                self._note_extension(version)
                app_log("extension connected " + (getattr(self, "ext_version", "") or "?"))
        elif event == "tab-query-failed":
            now = time.time()
            if now - getattr(self, "_tab_fail_log", 0) > 60:
                self._tab_fail_log = now
                app_log("tab query failed")
        elif event == "chat-detect":
            stage = message.get("stage")
            if stage not in ("found", "page", "no-messages", "filtered", "no-scroller", "inject"):
                stage = "no-messages"
            def count(key):
                try:
                    return max(0, min(999999, int(message.get(key) or 0)))
                except (TypeError, ValueError):
                    return 0
            if stage == "found":
                app_log(
                    "chat detect found messages %d candidates %d box %dx%d"
                    % (count("messages"), count("candidates"), count("width"), count("height"))
                )
            else:
                app_log(
                    "chat detect %s top %d roots %d nodes %d main %d article %d log %d "
                    "role %d msgid %d turntest %d turnid %d turnarticle %d turnsection %d dataturn %d testid %d "
                    "frames %d open %d blocked %d framenodes %d shadows %d capped %d "
                    "messages %d raw %d small %d nav %d"
                    % (
                        stage, count("top"), count("roots"), count("nodes"), count("mains"),
                        count("articles"), count("logs"), count("role"), count("msgid"),
                        count("turntest"), count("turnid"), count("turnarticle"), count("turnsection"),
                        count("dataturn"), count("testid"), count("frames"), count("frameopen"),
                        count("frameblocked"), count("framenodes"), count("shadows"), count("capped"),
                        count("messages"), count("raw"), count("small"), count("nav"),
                    )
                )

    def apply_tab_message(self, message):
        if not isinstance(message, dict):
            return
        host = message.get("host")
        if host not in ("chatgpt.com", "chat.openai.com", "other", ""):
            host = "other" if host else ""
        path = message.get("path")
        if path not in ("/", "/c", "/g", "/g/c", "/other", ""):
            path = "/other" if path else ""
        reason = message.get("reason")
        if reason not in ("hello", "menu", "event", "focus"):
            reason = ""
        self._note_extension(message.get("version"))
        tag = message.get("tag")
        if not isinstance(tag, str) or len(tag) != 8 or any(char not in "0123456789abcdef" for char in tag):
            tag = ""
        chat = bool(message.get("chat"))
        if not isinstance(getattr(self, "_browsers", None), dict):
            self._browsers = {}
        if tag:
            if getattr(self, "_refreshing", False):
                pending = getattr(self, "_refresh_browsers", None)
                if not isinstance(pending, dict):
                    pending = {}
                    self._refresh_browsers = pending
                pending[tag] = chat
                enabled = any(pending.values())
            else:
                self._browsers[tag] = chat
                if len(self._browsers) > 8:
                    self._browsers.pop(next(iter(self._browsers)))
                enabled = any(self._browsers.values())
        else:
            enabled = chat
        if chat:
            self._tab_place = (host, path, reason)
        self.chat_page = enabled
        self._tab_reply = time.time()
        if not getattr(self, "_refreshing", False):
            self._log_chat_menu(enabled, host, path, reason)

    def refresh_chat_menu(self):
        if self.busy or self.page_waiting or self.closing or self.bridge is None:
            return
        if self.chat_page:
            return
        try:
            connected = self.bridge.connected()
        except Exception:
            connected = False
        if not connected:
            if not self.chat_page:
                self._log_menu_gap("extension disconnected")
            return
        before = bool(self.chat_page)
        self._refreshing = True
        self._refresh_browsers = {}
        answered = False
        try:
            self.bridge.request_report()
            token = time.time()
            self._tab_reply = 0
            first = 0
            deadline = time.time() + 0.7
            while time.time() < deadline:
                self.take_idle_messages()
                replied = getattr(self, "_tab_reply", 0) >= token
                if replied and self.chat_page:
                    break
                if replied and not first:
                    first = time.time()
                if first and time.time() - first > 0.3:
                    break
                time.sleep(0.02)
            answered = bool(self._refresh_browsers) and getattr(self, "_tab_reply", 0) >= token
            if answered:
                merged = dict(self._browsers or {})
                merged.update(self._refresh_browsers)
                self._browsers = merged
                self.chat_page = any(merged.values())
        except Exception:
            app_log("chat menu report failed")
        finally:
            self._refreshing = False
        if answered:
            if self.chat_page:
                place = getattr(self, "_tab_place", ("", "", "menu"))
                self._log_chat_menu(True, place[0], place[1], place[2] if len(place) > 2 else "menu")
            elif before:
                self._log_chat_menu(False, "", "", "menu")
        if not self.chat_page:
            self._log_menu_gap("chat menu still off")

    def route_background_message(self, message):
        kind = message.get("type")
        if kind == "tab":
            self.apply_tab_message(message)
        elif kind == "diag" and message.get("event") == "live-arm" and os.environ.get("QUICKSHOT_LIVE_CHECK") == "1":
            mode = message.get("mode") if message.get("mode") in ("chat", "page") else "chat"
            self.capture_page(mode, announce=False)
        elif kind == "diag":
            self.apply_diag(message)
        elif kind == "request" and message.get("mode") == "chat" and not self.page_waiting:
            self.capture_page("chat")

    def take_idle_messages(self):
        if self.closing or self.busy or self.page_waiting or getattr(self, "bridge", None) is None:
            return
        try:
            messages = self.bridge.take_messages()
        except Exception:
            app_log(traceback.format_exc())
            return
        for message in messages:
            self.route_background_message(message)

    def capture_page(self, mode="page", announce=True):
        if self.busy or self.closing or self.page_waiting:
            return
        if self.bridge is None or not self.bridge.connected():
            app_log("page not connected")
            self.show_setup()
            return
        self.discard_page_messages()
        self.page_waiting = True
        self.page_mode = "chat" if mode == "chat" else "page"
        self.page_phase = "checking"
        self.page_started = time.time()
        self.page_path = None
        self.page_paths = []
        self.page_stamp = ""
        self.page_parts = 0
        self.page_text = ""
        self.page_done = False
        self.page_truncated = False
        self.page_partial = ""
        self.page_began = time.time()
        if announce:
            try:
                self.bridge.request_capture(self.page_mode)
            except Exception:
                app_log(traceback.format_exc())
                self.stop_page_wait()
                self.show_result(self.tr("page_failed"))
                return
            app_log("page request " + self.page_mode)
        else:
            app_log("page armed " + self.page_mode)
        self.show_result(self.tr("page_checking"), waiting=True)
        self.page_job = self.root.after(300, self.poll_page)

    def poll_page(self):
        if not self.page_waiting:
            return
        self.page_job = None
        try:
            self.read_page()
        except Exception:
            app_log(traceback.format_exc())
            self.stop_page_wait()
            self.show_result(self.tr("page_failed"))

    def read_page(self):
        failed = None
        if not isinstance(getattr(self, "page_paths", None), list):
            self.page_paths = []
        try:
            messages = self.bridge.take_messages() if self.bridge else []
        except Exception:
            app_log(traceback.format_exc())
            messages = []
        for message in messages:
            kind = message.get("type")
            if kind == "tab":
                self.apply_tab_message(message)
            elif kind == "diag":
                self.apply_diag(message)
            elif kind == "status":
                stage = str(message.get("stage") or "")
                if stage == "accepted":
                    app_log("page accepted")
                elif stage == "permission":
                    app_log("page permission")
                    failed = self.tr("page_permission")
                elif stage == "capturing":
                    app_log("page capturing")
                    self.page_phase = "capturing"
                    conceal = getattr(self, "conceal_panel", None)
                    if callable(conceal):
                        conceal()
                    withdraw = getattr(self, "withdraw_result", None)
                    if callable(withdraw):
                        withdraw()
            elif kind == "progress" and message.get("text"):
                self.page_started = time.time()
                if self.page_phase != "capturing":
                    app_log("page capturing")
                    self.page_phase = "capturing"
                    conceal = getattr(self, "conceal_panel", None)
                    if callable(conceal):
                        conceal()
                    withdraw = getattr(self, "withdraw_result", None)
                    if callable(withdraw):
                        withdraw()
            elif kind == "png":
                data = message.get("data") or b""
                try:
                    part = int(message.get("part") or 0)
                except (TypeError, ValueError):
                    part = 0
                app_log("page image %d" % len(data))
                try:
                    kind_name = "chat" if getattr(self, "page_mode", "page") == "chat" else "page"
                    if not self.page_paths:
                        self.page_stamp = pngsave.capture_stamp(kind_name)
                        path = pngsave.single_png(kind_name, self.page_stamp)
                    else:
                        if len(self.page_paths) == 1 and not self.page_paths[0].endswith("-001.png"):
                            renamed = pngsave.part_png(kind_name, self.page_stamp, 1)
                            os.replace(self.page_paths[0], renamed)
                            self.page_paths[0] = renamed
                        index = part if part >= 2 else len(self.page_paths) + 1
                        path = pngsave.part_png(kind_name, self.page_stamp, index)
                    with open(path, "wb") as handle:
                        handle.write(data)
                    self.page_paths.append(path)
                    self.page_path = self.page_paths[0]
                    app_log("page saved " + path)
                except Exception:
                    app_log(traceback.format_exc())
                    failed = self.tr("page_failed")
            elif kind == "error":
                raw = str(message.get("message") or "")
                if "activeTab" in raw or "<all_urls>" in raw:
                    app_log("page permission " + raw)
                else:
                    app_log("page error " + raw)
                failed = localize_extension_text(self.lang, raw or self.tr("page_failed"))
            elif kind == "done":
                self.page_done = True
                self.page_truncated = bool(message.get("truncated"))
                self.page_partial = str(message.get("partial") or "")
                try:
                    self.page_parts = int(message.get("parts") or 0)
                except (TypeError, ValueError):
                    self.page_parts = 0
                if self.page_partial:
                    app_log("page partial " + self.page_partial)
        if failed:
            paths = list(self.page_paths)
            self.stop_page_wait()
            if paths:
                text = self.tr("page_parts_partial").format(n=len(paths)) + "\n" + failed
                text += "\n" + "\n".join(paths)
                self.show_result(text, os.path.dirname(paths[0]), file=paths[0])
            else:
                self.show_result(failed)
            return
        if self.page_paths and self.page_done:
            paths = list(self.page_paths)
            expected = int(getattr(self, "page_parts", 0) or 0)
            partial = self.page_partial
            truncated = self.page_truncated
            incomplete = bool(partial) or truncated or (expected > 0 and len(paths) != expected)
            app_log("page done %s %d" % (getattr(self, "page_mode", "page"), len(paths)))
            self.stop_page_wait()
            if incomplete:
                if partial == "top":
                    label = self.tr("page_partial_top")
                elif partial == "bottom":
                    label = self.tr("page_partial_bottom")
                elif truncated and len(paths) == 1:
                    label = self.tr("page_truncated")
                else:
                    label = self.tr("page_partial_bottom")
                label += "\n" + self.tr("page_parts_partial").format(n=len(paths))
            elif len(paths) == 1:
                if getattr(self, "page_mode", "page") == "chat":
                    label = self.tr("chat_saved")
                else:
                    label = self.tr("page_saved")
            else:
                if getattr(self, "page_mode", "page") == "chat":
                    label = self.tr("chat_parts").format(n=len(paths))
                else:
                    label = self.tr("page_parts").format(n=len(paths))
                label += "\n" + self.tr("parts_no_copy")
            note = getattr(self, "note_capture", None)
            if callable(note):
                for index, one in enumerate(paths):
                    note(one, len(paths) == 1 and index == 0)
            self.show_result(label + "\n" + "\n".join(paths), os.path.dirname(paths[0]), file=paths[0])
            return
        elapsed = time.time() - self.page_started
        began = getattr(self, "page_began", self.page_started)
        if time.time() - began > 600:
            self.stop_page_wait()
            app_log("page timeout")
            self.show_result(self.tr("page_timeout"))
            return
        if self.page_phase != "capturing" and elapsed > 8:
            self.stop_page_wait()
            app_log("page no response")
            self.show_result(self.tr("page_no_response"))
            return
        if elapsed > 90:
            self.stop_page_wait()
            app_log("page timeout")
            self.show_result(self.tr("page_timeout"))
            return
        if self.page_waiting:
            self.page_job = self.root.after(300, self.poll_page)

    def setup_body(self):
        return self.tr("page_setup").replace("{folder}", self.extension_dir or "")

    def refresh_setup(self):
        if self.setup is None or self.setup_label is None:
            return
        try:
            if not self.setup.winfo_exists():
                self.setup = None
                self.setup_label = None
                return
            self.setup.title(self.tr("page_setup_title"))
            self.setup_label.configure(text=self.setup_body())
            self.setup_close.configure(text=self.tr("close"))
        except tk.TclError:
            self.setup = None
            self.setup_label = None

    def show_setup(self):
        if self.setup is not None:
            try:
                self.refresh_setup()
                self.setup.lift()
                return
            except tk.TclError:
                self.setup = None
                self.setup_label = None
        window = tk.Toplevel(self.root)
        window.title(self.tr("page_setup_title"))
        window.configure(bg="white")
        window.geometry("520x390")
        window.attributes("-topmost", True)
        self.setup_label = tk.Label(
            window, text=self.setup_body(), bg="white", justify="left",
            wraplength=480, padx=16, pady=16,
        )
        self.setup_label.pack(fill="both", expand=True)
        self.setup_close = tk.Button(window, text=self.tr("close"), command=self.close_setup)
        self.setup_close.pack(pady=(0, 12))
        self.setup = window
        window.protocol("WM_DELETE_WINDOW", self.close_setup)

    def close_setup(self):
        if self.setup is not None:
            try:
                self.setup.destroy()
            except tk.TclError:
                pass
            self.setup = None
            self.setup_label = None

    def hide_button(self):
        self.conceal_panel()

    def show_button(self):
        self.reveal_panel()
        self.lift_dialogs()
        self.root.update_idletasks()

    def conceal_panel(self):
        if not self._panel_concealed:
            app_log("panel hide")
        self._panel_concealed = True
        self.hide_tip()
        win = getattr(self, "win", None)
        if win is None:
            return
        win.withdraw()
        self.root.update()

    def reveal_panel(self):
        hidden = bool(self._panel_concealed)
        self._panel_concealed = False
        win = getattr(self, "win", None)
        if win is None or self.closing:
            return
        win.deiconify()
        self.apply_topmost()
        if hidden:
            app_log("panel show")

    def withdraw_result(self):
        if self.result is None:
            return
        try:
            self.result.withdraw()
        except tk.TclError:
            self.result = None

    def apply_topmost(self):
        win = getattr(self, "win", None)
        if win is None:
            return
        enabled = bool(getattr(self, "always_top", True)) and not getattr(self, "_panel_concealed", False)
        try:
            win.attributes("-topmost", enabled)
        except tk.TclError:
            return
        try:
            capture.hold_topmost(int(win.winfo_id()), enabled)
        except Exception:
            app_log(traceback.format_exc())

    def keep_top(self):
        if self.closing:
            return
        try:
            visible = bool(self.win.winfo_viewable())
        except tk.TclError:
            return
        if not self._panel_concealed and not visible:
            app_log("panel restore")
            self.reveal_panel()
        elif self.always_top and not self._panel_concealed:
            self.apply_topmost()
        self.take_idle_messages()
        try:
            self.root.after(1200, self.keep_top)
        except tk.TclError:
            pass

    def poll_hotkeys(self):
        if self.closing:
            return
        try:
            if self._hotkey is not None and not self.busy and not self.page_waiting:
                for ident in self._hotkey.poll():
                    now = time.time()
                    if now - self._hot_at < 0.45:
                        continue
                    self._hot_at = now
                    if ident == 1:
                        self.begin_select()
                    elif ident == 2:
                        self.capture_screen()
                    elif ident == 3:
                        self.capture_page()
                    break
        except Exception:
            app_log(traceback.format_exc())
        try:
            self.root.after(80, self.poll_hotkeys)
        except tk.TclError:
            pass

    def note_capture(self, path, copy=True):
        if not path or not getattr(self, "win", None):
            return
        try:
            import history
            history.add(path)
        except Exception:
            app_log("history failed " + traceback.format_exc())
        if not copy or not self.copy_images:
            return
        try:
            import imageutil
            imageutil.copy_png_file(path)
            app_log("clipboard copied " + path)
        except Exception:
            app_log("clipboard failed " + traceback.format_exc())

    def open_result_ocr(self):
        if self.result_path:
            self.show_ocr(self.result_path)

    def open_result_edit(self):
        if self.result_path:
            self.show_editor(self.result_path)

    def begin_select(self):
        if self.busy or self.closing:
            return
        if self.page_waiting:
            app_log("page cancel")
            self.stop_page_wait()
        self.busy = True
        try:
            self.close_toast()
            self.hide_button()
            self.open_overlay()
        except Exception:
            app_log(traceback.format_exc())
            if self.busy and not self.closing:
                self.finish(None)
            self.show_toast("failed")

    def open_overlay(self):
        vx, vy, vw, vh = capture.virtual_screen()
        overlay = tk.Toplevel(self.root)
        overlay.withdraw()
        self.overlay = overlay
        overlay.overrideredirect(True)
        overlay.configure(bg="black", cursor="crosshair")
        overlay.geometry(f"{int(vw)}x{int(vh)}+{int(vx)}+{int(vy)}")
        overlay.attributes("-alpha", 0.30)
        overlay.attributes("-topmost", True)
        canvas = tk.Canvas(
            overlay, bg="black", highlightthickness=0, borderwidth=0, cursor="crosshair"
        )
        canvas.pack(fill="both", expand=True)
        self.canvas = canvas
        self.rect_id = None
        self.sel_start = None
        canvas.bind("<ButtonPress-1>", self.on_sel_down)
        canvas.bind("<B1-Motion>", self.on_sel_move)
        canvas.bind("<ButtonRelease-1>", self.on_sel_up)
        canvas.bind("<Button-3>", lambda _event: self.finish(None))
        self.root.bind_all("<Escape>", self.on_escape)
        overlay.deiconify()
        overlay.update_idletasks()
        overlay.attributes("-alpha", 0.30)
        overlay.attributes("-topmost", True)
        overlay.lift()
        overlay.focus_force()
        try:
            overlay.grab_set()
        except tk.TclError:
            pass

    def on_escape(self, _event=None):
        if self.busy:
            self.finish(None)
        return "break"

    def on_sel_down(self, event):
        self.sel_start = (event.x_root, event.y_root)
        self.draw_selection(event.x_root, event.y_root)

    def on_sel_move(self, event):
        if self.sel_start:
            self.draw_selection(event.x_root, event.y_root)

    def on_sel_up(self, event):
        if not self.sel_start:
            self.finish(None)
            return
        x1, y1 = self.sel_start
        x2, y2 = event.x_root, event.y_root
        self.sel_start = None
        self.finish((min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)))

    def draw_selection(self, x2, y2):
        if not self.canvas or not self.overlay or not self.sel_start:
            return
        origin_x = self.overlay.winfo_rootx()
        origin_y = self.overlay.winfo_rooty()
        x1, y1 = self.sel_start
        coords = (x1 - origin_x, y1 - origin_y, x2 - origin_x, y2 - origin_y)
        if self.rect_id:
            self.canvas.coords(self.rect_id, *coords)
        else:
            self.rect_id = self.canvas.create_rectangle(*coords, outline="white", width=2)

    def pump(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.root.update()
            time.sleep(0.02)

    def hide_overlay(self):
        if self.overlay is None:
            return
        try:
            self.overlay.grab_release()
        except tk.TclError:
            pass
        self.overlay.withdraw()
        self.root.update()

    def destroy_overlay(self):
        try:
            self.root.unbind_all("<Escape>")
        except tk.TclError:
            pass
        if self.overlay is not None:
            try:
                self.overlay.destroy()
            except tk.TclError:
                pass
        self.overlay = None
        self.canvas = None
        self.rect_id = None
        self.sel_start = None

    def finish(self, rect):
        if self.closing or not self.busy:
            return
        self.closing = True
        self.busy = False
        failed = False
        copied = False
        try:
            self.hide_overlay()
            self.withdraw_result()
            if rect is not None:
                x, y, width, height = clamp_rect(rect[0], rect[1], rect[2], rect[3])
                if width >= 3 and height >= 3:
                    self.pump(0.16)
                    if self.win.winfo_viewable():
                        app_log("panel still visible")
                    path = pngsave.unique_png("area")
                    with open(path, "wb") as handle:
                        handle.write(pngsave.dib_to_png(capture.capture_region(x, y, width, height)))
                    copied = path
                    app_log("area saved " + path)
        except Exception:
            app_log(traceback.format_exc())
            failed = True
        finally:
            self.destroy_overlay()
            self.closing = False
            self.show_button()
            if failed:
                self.show_toast("failed")
            elif copied:
                self.note_capture(copied)
                self.show_result(self.tr("area_saved") + "\n" + copied, os.path.dirname(copied), file=copied)

    def show_history(self):
        try:
            import history
        except Exception:
            app_log(traceback.format_exc())
            return
        if self.history_window is not None:
            try:
                if self.history_window.winfo_exists():
                    self.history_window.lift()
                    return
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        window.title(self.tr("history"))
        window.geometry("640x420")
        window.attributes("-topmost", True)
        window.configure(bg="white")
        self.history_window = window
        listing = tk.Listbox(window, width=42, activestyle="dotbox")
        listing.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)
        side = tk.Frame(window, bg="white")
        side.pack(side="left", fill="both", expand=True, padx=(4, 8), pady=8)
        thumb = tk.Label(side, bg="white")
        thumb.pack(anchor="w")
        detail = tk.Label(side, bg="white", justify="left", wraplength=250, anchor="w")
        detail.pack(anchor="w", pady=(6, 8))
        items = {"rows": history.load()}

        def selected():
            index = listing.curselection()
            if not index:
                return None
            rows = items["rows"]
            if index[0] >= len(rows):
                return None
            return rows[index[0]]

        def show_selected(_event=None):
            row = selected()
            if not row:
                return
            exists = os.path.isfile(row.get("path", ""))
            when = time.strftime("%Y-%m-%d %H:%M", time.localtime(row.get("time") or 0))
            size = int(row.get("bytes") or 0)
            text = "%s\n%s\n%s×%s\n%s KB\n%s" % (
                os.path.basename(row.get("path", "")),
                when,
                row.get("w") or "?",
                row.get("h") or "?",
                max(1, size // 1024) if exists else 0,
                row.get("path", "") if exists else self.tr("history_missing"),
            )
            detail.configure(text=text)
            thumb.configure(image="")
            thumb.image = None
            picture = row.get("thumb") or ""
            if picture and os.path.isfile(picture):
                try:
                    image = tk.PhotoImage(file=picture)
                    thumb.configure(image=image)
                    thumb.image = image
                except tk.TclError:
                    pass

        def refill():
            listing.delete(0, "end")
            items["rows"] = history.load()
            for row in items["rows"]:
                name = os.path.basename(row.get("path", ""))
                if not os.path.isfile(row.get("path", "")):
                    name = "× " + name
                listing.insert("end", name)
            if items["rows"]:
                listing.selection_set(0)
                show_selected()
            else:
                detail.configure(text=self.tr("no_history"))

        def open_image():
            row = selected()
            if not row or not os.path.isfile(row.get("path", "")):
                self.show_notice(self.tr("history_missing"))
                return
            os.startfile(row["path"])

        def open_folder():
            row = selected()
            if not row:
                return
            folder = os.path.dirname(row.get("path", ""))
            if os.path.isdir(folder):
                os.startfile(folder)

        def copy_selected():
            row = selected()
            if not row or not os.path.isfile(row.get("path", "")):
                self.show_notice(self.tr("history_missing"))
                return
            self.note_capture(row["path"])

        def edit_selected():
            row = selected()
            if not row or not os.path.isfile(row.get("path", "")):
                self.show_notice(self.tr("history_missing"))
                return
            self.show_editor(row["path"])

        def forget_selected():
            row = selected()
            if not row:
                return
            history.forget(row.get("path", ""))
            refill()

        def delete_selected():
            row = selected()
            if not row:
                return
            path = row.get("path", "")
            if not os.path.isfile(path):
                history.forget(path)
                refill()
                return
            if not messagebox.askyesno(self.tr("history"), self.tr("history_confirm"), parent=window):
                return
            try:
                os.remove(path)
            except OSError:
                app_log(traceback.format_exc())
                self.show_notice(self.tr("folder_failed"))
                return
            history.forget(path)
            refill()

        listing.bind("<<ListboxSelect>>", show_selected)
        actions = tk.Frame(side, bg="white")
        actions.pack(anchor="w")
        tk.Button(actions, text=self.tr("open_image"), command=open_image).pack(fill="x", pady=2)
        tk.Button(actions, text=self.tr("open_folder"), command=open_folder).pack(fill="x", pady=2)
        tk.Button(actions, text=self.tr("copy_button"), command=copy_selected).pack(fill="x", pady=2)
        tk.Button(actions, text=self.tr("edit"), command=edit_selected).pack(fill="x", pady=2)
        tk.Button(actions, text=self.tr("history_forget"), command=forget_selected).pack(fill="x", pady=2)
        tk.Button(actions, text=self.tr("history_delete"), command=delete_selected).pack(fill="x", pady=2)
        refill()
        window.protocol("WM_DELETE_WINDOW", lambda: close_history())

        def close_history():
            self.history_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass

    def show_ocr(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                parent=self.root,
                filetypes=[("PNG", "*.png"), ("Images", "*.png *.jpg *.jpeg *.bmp")],
                title=self.tr("ocr"),
            )
        if not path:
            return
        if self.ocr_window is not None:
            try:
                if self.ocr_window.winfo_exists():
                    self.ocr_window.destroy()
            except tk.TclError:
                pass
        window = tk.Toplevel(self.root)
        window.title(self.tr("ocr"))
        window.geometry("560x420")
        window.attributes("-topmost", True)
        self.ocr_window = window
        app_log("ocr open")

        def close_ocr():
            app_log("ocr close")
            self.ocr_window = None
            try:
                window.destroy()
            except tk.TclError:
                pass
            if not self._panel_concealed and not self.closing:
                self.reveal_panel()

        window.protocol("WM_DELETE_WINDOW", close_ocr)
        box = tk.Text(window, wrap="word", font=("Segoe UI", 11))
        box.pack(fill="both", expand=True, padx=8, pady=(8, 4))
        box.insert("1.0", self.tr("ocr_working"))
        bar = tk.Frame(window)
        bar.pack(fill="x", padx=8, pady=(0, 8))

        def copy_text():
            text = box.get("1.0", "end").strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.show_notice(self.tr("copied"))

        def save_text():
            dest = filedialog.asksaveasfilename(
                parent=window, defaultextension=".txt", filetypes=[("Text", "*.txt")],
                title=self.tr("save_text"),
            )
            if not dest:
                return
            with open(dest, "w", encoding="utf-8") as handle:
                handle.write(box.get("1.0", "end").strip())

        tk.Button(bar, text=self.tr("copy_text"), command=copy_text).pack(side="left", padx=(0, 8))
        tk.Button(bar, text=self.tr("save_text"), command=save_text).pack(side="left")

        def worker():
            try:
                import ocr
                text = ocr.recognize(path) or ""
                if not text:
                    text = self.tr("ocr_failed")
            except Exception as exc:
                app_log("ocr failed " + traceback.format_exc())
                message = str(exc)
                text = self.tr("ocr_missing") if "QS_OCR_UNAVAILABLE" in message else self.tr("ocr_failed")

            def show():
                try:
                    if window.winfo_exists():
                        box.delete("1.0", "end")
                        box.insert("1.0", text)
                except tk.TclError:
                    pass

            try:
                self.root.after(0, show)
            except tk.TclError:
                pass

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def show_editor(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                parent=self.root,
                filetypes=[("PNG", "*.png")],
                title=self.tr("edit"),
            )
        if not path:
            return
        app_log("editor open")
        try:
            import editor
            opened = editor.open_editor(self.root, path, self.tr, on_close=self._editor_closed)
        except Exception:
            app_log(traceback.format_exc())
            self.show_notice(self.tr("edit_large"))
            return
        if opened == "large":
            self.show_notice(self.tr("edit_large"))
            return
        self.editor_window = opened

    def _editor_closed(self):
        app_log("editor close")
        self.editor_window = None
        if not self._panel_concealed and not self.closing:
            self.reveal_panel()

    def quit(self):
        self.closing = True
        self.stop_page_wait()
        if self._hotkey is not None:
            try:
                self._hotkey.unregister()
            except Exception:
                app_log(traceback.format_exc())
        app_log("gui exit " + process_note())
        if capture.tray_remove():
            app_log("tray remove")
        self.save_settings()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    if "--native-host" in sys.argv or (getattr(sys, "frozen", False) and bridge.stdio_is_pipe()):
        bridge.run_native_host()
        return 0
    if sys.platform != "win32":
        print("QuickShot supports Windows only.")
        return 1
    if not capture.acquire_single_instance():
        app_log("gui blocked duplicate " + process_note())
        lang = peek_lang()
        capture.user32.MessageBoxW(
            None,
            STRINGS[lang]["already"],
            "QuickShot",
            0x00000040 | 0x00010000 | 0x00040000,
        )
        return 2
    def _unhandled(etype, value, tb):
        app_log("unhandled " + "".join(traceback.format_exception(etype, value, tb))[:800])

    sys.excepthook = _unhandled
    try:
        App().run()
    except Exception as exc:
        app_log(traceback.format_exc())
        capture.user32.MessageBoxW(None, str(exc)[:500], "QuickShot", 0x00000010)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
