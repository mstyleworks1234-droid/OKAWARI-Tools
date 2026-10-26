import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import tkinter as tk

import main
import pngsave


class LanguageTests(unittest.TestCase):
    def test_both_languages_cover_the_same_keys(self):
        self.assertEqual(set(main.STRINGS["ja"]), set(main.STRINGS["en"]))
        self.assertNotEqual(main.STRINGS["ja"]["select"], main.STRINGS["en"]["select"])
        self.assertNotEqual(main.STRINGS["ja"]["exit"], main.STRINGS["en"]["exit"])
        self.assertIn("{folder}", main.STRINGS["ja"]["page_setup"])
        self.assertIn("{folder}", main.STRINGS["en"]["page_setup"])

    def test_extension_messages_follow_the_selected_language(self):
        japanese = "表示中のページが見つかりません。"
        self.assertEqual(main.localize_extension_text("ja", japanese), japanese)
        self.assertEqual(
            main.localize_extension_text("en", japanese),
            "No visible page was found.",
        )
        self.assertEqual(main.localize_extension_text("ja", "撮影中 2"), "撮影中 2")
        self.assertEqual(main.localize_extension_text("en", "撮影中 2"), "Capturing 2")
        self.assertEqual(main.localize_extension_text("en", "other"), "other")
        missing = "会話本文の領域を特定できませんでした。通常のページ全体撮影は使えます。"
        self.assertIn("Full-page", main.localize_extension_text("en", missing))
        self.assertEqual(main.localize_extension_text("ja", missing), missing)
        raw = "Either the '<all_urls>' or 'activeTab' permission is required."
        self.assertNotIn("activeTab", main.localize_extension_text("ja", raw))
        self.assertIn("permission", main.localize_extension_text("en", raw).lower())

    def test_saved_language_is_restored(self):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "settings.json")

        class Holder:
            pos = (10, 20)
            lang = "en"

        with patch.object(main, "settings_path", lambda: path):
            main.App.save_settings(Holder())
            self.assertEqual(main.peek_lang(), "en")
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["lang"], "en")
            Holder.lang = "ja"
            Holder.save_dir = folder
            main.App.save_settings(Holder())
            self.assertEqual(main.peek_lang(), "ja")
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["dir"], folder)


class FakePageBridge:
    def __init__(self, messages):
        self.messages = list(messages)
        self.requested = False

    def connected(self):
        return True

    def request_capture(self, mode="page"):
        self.requested = True
        self.mode = mode

    def take_messages(self):
        items = self.messages
        self.messages = []
        return items


class PageWaitHarness:
    lang = "ja"
    busy = False
    closing = False
    page_waiting = False
    page_phase = ""
    page_job = None
    page_started = 0
    page_path = None
    page_done = False
    page_truncated = False
    shown = None

    def __init__(self, messages):
        self.bridge = FakePageBridge(messages)
        self.shown = []
        self.root = type("Root", (), {"after": lambda *args: None})()
        self.discard_page_messages = lambda: main.App.discard_page_messages(self)
        self.stop_page_wait = lambda: main.App.stop_page_wait(self)
        self.poll_page = lambda: None

    def tr(self, key):
        return main.STRINGS[self.lang][key]

    def show_result(self, text, folder=None, waiting=False, file=None):
        self.shown.append((text, folder, waiting))


class PageWaitTests(unittest.TestCase):
    def test_checking_does_not_claim_capture_started_or_block_the_panel(self):
        app = PageWaitHarness([])
        main.App.capture_page(app)
        self.assertTrue(app.bridge.requested)
        self.assertTrue(app.page_waiting)
        self.assertFalse(app.busy)
        self.assertEqual(app.page_phase, "checking")
        self.assertEqual(app.bridge.mode, "page")
        self.assertEqual(app.shown[0][0], "接続を確認しています")

    def test_chat_capture_asks_for_the_conversation_mode(self):
        app = PageWaitHarness([])
        main.App.capture_page(app, "chat")
        self.assertEqual(app.bridge.mode, "chat")
        self.assertEqual(app.page_mode, "chat")
        self.assertFalse(app.busy)
        self.assertTrue(app.shown[0][2])

    def test_permission_failure_replaces_the_checking_message(self):
        raw = "Either the '<all_urls>' or 'activeTab' permission is required."
        app = PageWaitHarness([
            {"type": "status", "stage": "accepted"},
            {"type": "status", "stage": "permission"},
            {"type": "error", "message": raw},
        ])
        app.page_waiting = True
        app.page_phase = "checking"
        app.page_started = time.time()
        main.App.read_page(app)
        self.assertFalse(app.page_waiting)
        self.assertFalse(app.busy)
        self.assertNotIn("activeTab", app.shown[-1][0])
        self.assertIn("権限", app.shown[-1][0])
        self.assertFalse(app.shown[-1][2])
        app.lang = "en"
        app.page_waiting = True
        app.page_phase = "checking"
        app.page_started = time.time()
        app.bridge.messages = [
            {"type": "status", "stage": "permission"},
            {"type": "error", "message": raw},
        ]
        main.App.read_page(app)
        self.assertIn("permission", app.shown[-1][0].lower())
        self.assertNotIn("権限", app.shown[-1][0])

    def test_silence_ends_without_leaving_the_panel_busy(self):
        app = PageWaitHarness([])
        app.page_waiting = True
        app.page_phase = "checking"
        app.page_started = time.time() - 9
        main.App.read_page(app)
        self.assertFalse(app.page_waiting)
        self.assertFalse(app.busy)
        self.assertIn("応答がありません", app.shown[-1][0])

    def test_capturing_text_starts_only_after_the_extension_says_so(self):
        app = PageWaitHarness([{"type": "status", "stage": "capturing"}])
        app.page_waiting = True
        app.page_phase = "checking"
        app.page_started = time.time()
        main.App.read_page(app)
        self.assertEqual(app.page_phase, "capturing")
        self.assertEqual(app.shown, [])

    def test_png_message_is_saved_before_the_dialog_reports_success(self):
        folder = tempfile.mkdtemp()
        previous = pngsave._custom_dir
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        try:
            self.assertTrue(pngsave.set_output_dir(folder))
            app = PageWaitHarness([
                {"type": "png", "data": png},
                {"type": "done", "truncated": False},
            ])
            app.page_waiting = True
            app.page_phase = "capturing"
            app.page_started = time.time()
            main.App.read_page(app)
            self.assertFalse(app.page_waiting)
            self.assertIn("ページ全体を保存しました", app.shown[-1][0])
            self.assertEqual(app.shown[-1][1], folder)
            self.assertFalse(app.shown[-1][2])
            saved = [name for name in os.listdir(folder) if name.startswith("QuickShot-page-")]
            self.assertEqual(len(saved), 1)
            self.assertNotIn("-001.png", saved[0])
            with open(os.path.join(folder, saved[0]), "rb") as handle:
                self.assertTrue(handle.read().startswith(b"\x89PNG\r\n\x1a\n"))
        finally:
            pngsave._custom_dir = previous

    def test_split_pages_are_numbered_and_are_not_one_clipboard_image(self):
        folder = tempfile.mkdtemp()
        previous = pngsave._custom_dir
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        copied = []
        try:
            self.assertTrue(pngsave.set_output_dir(folder))
            app = PageWaitHarness([
                {"type": "png", "data": png, "part": 1},
                {"type": "png", "data": png, "part": 2},
                {"type": "done", "truncated": False, "parts": 2},
            ])
            app.page_waiting = True
            app.page_phase = "capturing"
            app.page_started = time.time()
            app.page_mode = "chat"
            app.note_capture = lambda path, copy=True: copied.append(copy)
            main.App.read_page(app)
            text = app.shown[-1][0]
            self.assertNotIn("ページ全体を保存しました", text)
            self.assertNotIn("ChatGPTの会話を保存しました", text)
            self.assertIn("2枚に分けて最後まで保存しました", text)
            self.assertIn("クリップボードにはコピーしていません", text)
            names = sorted(name for name in os.listdir(folder) if name.startswith("QuickShot-chat-"))
            self.assertEqual(len(names), 2)
            self.assertTrue(names[0].endswith("-001.png"))
            self.assertTrue(names[1].endswith("-002.png"))
            self.assertEqual(copied, [False, False])
        finally:
            pngsave._custom_dir = previous

    def test_incomplete_split_is_not_reported_as_success(self):
        folder = tempfile.mkdtemp()
        previous = pngsave._custom_dir
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
            b"\x00\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        try:
            self.assertTrue(pngsave.set_output_dir(folder))
            app = PageWaitHarness([
                {"type": "png", "data": png, "part": 1},
                {"type": "error", "message": "画像の受け渡しに失敗しました。", "saved": 1},
            ])
            app.page_waiting = True
            app.page_phase = "capturing"
            app.page_started = time.time()
            app.page_mode = "page"
            main.App.read_page(app)
            text = app.shown[-1][0]
            self.assertNotIn("ページ全体を保存しました", text)
            self.assertIn("1枚まで保存しました", text)
            self.assertIn("続きは保存できていません", text)
            self.assertEqual(len(os.listdir(folder)), 1)
        finally:
            pngsave._custom_dir = previous


class MenuCommandTests(unittest.TestCase):
    def test_deferred_choice_survives_menu_destroy(self):
        root = tk.Tk()
        root.withdraw()
        choice = {}
        menu = tk.Menu(root, tearoff=0)
        menu.add_command(label="English", command=lambda: choice.__setitem__("action", "en"))
        root.after_idle(menu.invoke, 0)
        try:
            self.assertEqual(main.finish_menu(root, menu, choice), "en")
        finally:
            root.destroy()

    def test_click_switches_to_english_and_back(self):
        root = tk.Tk()
        root.geometry("160x80+240+240")
        root.update()
        labels = {}

        def open_menu(lang, point):
            menu = tk.Menu(root, tearoff=0)
            choice = {}
            menu.add_command(
                label=main.STRINGS[lang]["select"],
                command=lambda: choice.__setitem__("action", "select"),
            )
            menu.add_command(label="日本語", command=lambda: choice.__setitem__("action", "ja"))
            menu.add_command(label="English", command=lambda: choice.__setitem__("action", "en"))
            labels["first"] = menu.entrycget(0, "label")
            click_menu_item(2 if lang == "ja" else 1)
            cancel_menu_later(3.0)
            try:
                menu.tk_popup(*point)
                return main.finish_menu(root, menu, choice), labels["first"]
            finally:
                try:
                    menu.destroy()
                except tk.TclError:
                    pass

        try:
            action, first = open_menu("ja", (260, 260))
            self.assertEqual(action, "en")
            self.assertEqual(first, "範囲を選択して撮影")
            action, first = open_menu("en", (260, 300))
            self.assertEqual(action, "ja")
            self.assertEqual(first, "Select an area and capture")
        finally:
            root.destroy()


def cancel_menu_later(seconds):
    def worker():
        import ctypes

        time.sleep(seconds)
        user32 = ctypes.windll.user32
        hwnd = find_menu_window(user32)
        if hwnd:
            user32.PostMessageW(hwnd, 0x001F, 0, 0)

    threading.Thread(target=worker, daemon=True).start()


def click_menu_item(index):
    def worker():
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.SendMessageW.restype = ctypes.c_void_p
        user32.GetMenuItemRect.argtypes = [
            wintypes.HWND, ctypes.c_void_p, wintypes.UINT, ctypes.POINTER(wintypes.RECT)
        ]
        user32.GetMenuItemRect.restype = wintypes.BOOL
        time.sleep(0.35)
        hwnd = find_menu_window(user32)
        if not hwnd:
            return
        hmenu = user32.SendMessageW(hwnd, 0x01E1, 0, 0)
        rect = wintypes.RECT()
        ok = bool(hmenu) and bool(user32.GetMenuItemRect(None, hmenu, index, ctypes.byref(rect)))
        if not ok:
            user32.PostMessageW(hwnd, 0x001F, 0, 0)
            return
        x = (rect.left + rect.right) // 2
        y = (rect.top + rect.bottom) // 2
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        ax = int(x * 65535 / max(1, width - 1))
        ay = int(y * 65535 / max(1, height - 1))
        user32.mouse_event(0x8001, ax, ay, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(0x8002, ax, ay, 0, 0)
        time.sleep(0.05)
        user32.mouse_event(0x8004, ax, ay, 0, 0)

    threading.Thread(target=worker, daemon=True).start()


def find_menu_window(user32):
    import ctypes
    from ctypes import wintypes

    found = []

    def visit(hwnd, _data):
        class_name = ctypes.create_unicode_buffer(64)
        user32.GetClassNameW(hwnd, class_name, 64)
        if class_name.value == "#32768" and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    callback = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(callback(visit), 0)
    return found[0] if found else None


class ChatMenuTests(unittest.TestCase):
    def harness(self, messages):
        app = PageWaitHarness(messages)
        app.chat_page = False
        app.closing = False
        for name in (
            "apply_tab_message",
            "apply_diag",
            "_note_extension",
            "_log_chat_menu",
            "_log_menu_gap",
            "take_idle_messages",
            "route_background_message",
            "refresh_chat_menu",
        ):
            setattr(app, name, getattr(main.App, name).__get__(app))
        return app

    def test_chatgpt_page_enables_the_menu_before_capture(self):
        app = self.harness([])
        for path in ("/", "/c", "/g", "/g/c"):
            main.App.apply_tab_message(app, {
                "type": "tab",
                "chat": True,
                "host": "chatgpt.com",
                "path": path,
                "tag": "abcdef12",
                "version": "1.1.14",
                "reason": "event",
            })
            self.assertTrue(app.chat_page, path)

    def test_old_openai_host_enables_the_menu(self):
        app = self.harness([])
        main.App.apply_tab_message(app, {
            "type": "tab",
            "chat": True,
            "host": "chat.openai.com",
            "path": "/",
            "tag": "abcdef12",
            "reason": "hello",
        })
        self.assertTrue(app.chat_page)

    def test_same_browser_leaving_chatgpt_disables_the_menu(self):
        app = self.harness([])
        main.App.apply_tab_message(app, {
            "type": "tab", "chat": True, "host": "chatgpt.com", "path": "/c",
            "tag": "abcdef12", "reason": "event",
        })
        main.App.apply_tab_message(app, {
            "type": "tab", "chat": False, "host": "other", "path": "",
            "tag": "abcdef12", "reason": "event",
        })
        self.assertFalse(app.chat_page)

    def test_another_browser_does_not_disable_chatgpt(self):
        app = self.harness([])
        main.App.apply_tab_message(app, {
            "type": "tab", "chat": True, "host": "chatgpt.com", "path": "/c",
            "tag": "abcdef12", "reason": "event",
        })
        main.App.apply_tab_message(app, {
            "type": "tab", "chat": False, "host": "other", "path": "",
            "tag": "1234abcd", "reason": "event",
        })
        self.assertTrue(app.chat_page)

    def test_private_host_text_is_not_kept(self):
        app = self.harness([])
        main.App.apply_tab_message(app, {
            "type": "tab",
            "chat": False,
            "host": "https://user.example/secret",
            "path": "/private-id",
            "tag": "abcdef12",
            "reason": "event",
        })
        self.assertFalse(app.chat_page)
        self.assertNotIn("secret", str(getattr(app, "_tab_place", "")))

    def test_tab_report_during_capture_still_enables_the_menu(self):
        app = self.harness([{
            "type": "tab",
            "chat": True,
            "host": "chatgpt.com",
            "path": "/g/c",
            "tag": "abcdef12",
            "reason": "event",
        }])
        app.page_waiting = True
        app.page_phase = "capturing"
        app.page_started = time.time()
        app.page_paths = []
        app.page_done = False
        main.App.read_page(app)
        self.assertTrue(app.chat_page)
        self.assertTrue(app.page_waiting)

    def test_refresh_keeps_chatgpt_when_another_browser_answers_first(self):
        app = self.harness([])
        app.chat_page = True
        app._browsers = {"abcdef12": True}
        app._tab_place = ("chatgpt.com", "/c", "event")

        class Bridge:
            def connected(self):
                return True

            def request_report(self):
                return None

            def take_messages(self):
                return [{
                    "type": "tab",
                    "chat": False,
                    "host": "other",
                    "path": "",
                    "tag": "1234abcd",
                    "reason": "menu",
                }]

        app.bridge = Bridge()
        main.App.refresh_chat_menu(app)
        self.assertTrue(app.chat_page)

    def test_result_dialog_is_not_given_a_fractional_alpha(self):
        root = tk.Tk()
        root.withdraw()
        window = tk.Toplevel(root)
        window.withdraw()
        try:
            main.App.make_opaque(object(), window)
            window.deiconify()
            main.App.make_opaque(object(), window)
            self.assertEqual(float(window.attributes("-alpha")), 1.0)
        finally:
            window.destroy()
            root.destroy()


if __name__ == "__main__":
    unittest.main()
