"""QuickShot: a small always-on-top button that copies a screen region."""

import capture

capture.enable_dpi_awareness()

import json
import os
import sys
import time
import tkinter as tk

import bridge
import pngsave

VERSION = "1.1.0"

STRINGS = {
    "ja": {
        "exit": "終了",
        "copied": "コピーしました",
        "failed": "コピーに失敗しました",
        "tip": "上: 範囲  中: 画面全体  下: ページ全体",
        "already": "QuickShot はすでに起動しています。",
        "screen": "画面全体を保存",
        "page": "ページ全体を保存",
        "saved_one": "画面全体を保存しました",
        "saved_many": "{n}台の画面を1枚に保存しました",
        "screen_failed": "画面全体の保存に失敗しました",
        "screen_large": "画面が広すぎて1枚に保存できません",
        "page_start": "ページを上から撮影しています",
        "page_saved": "ページ全体を保存しました",
        "page_truncated": "ページが長いため、上から一部まで保存しました",
        "page_failed": "ページ全体の撮影に失敗しました",
        "page_timeout": "ページ全体の撮影が完了しませんでした",
        "page_setup_title": "ページ全体の初回設定",
    },
    "en": {
        "exit": "Exit",
        "copied": "Copied",
        "failed": "Copy failed",
        "tip": "Top: area  Middle: screen  Bottom: page",
        "already": "QuickShot is already running.",
        "screen": "Save entire screen",
        "page": "Save entire page",
        "saved_one": "Saved the entire screen",
        "saved_many": "Saved {n} monitors as one image",
        "screen_failed": "Could not save the entire screen",
        "screen_large": "The desktop is too large to save as one image",
        "page_start": "Capturing the page from the top",
        "page_saved": "Saved the entire page",
        "page_truncated": "The page was long, so only the top portion was saved",
        "page_failed": "Could not capture the entire page",
        "page_timeout": "The page capture did not finish",
        "page_setup_title": "One-time page capture setup",
    },
}


def settings_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    folder = os.path.join(base, "OKAWARI", "QuickShot")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def button_size(dpi):
    return max(48, int(round(52 * (dpi or 96) / 96)))


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
    size = button_size(dpi)
    x = right - size - 16
    y = top + max(0, (bottom - top - size) // 2)
    x, y, dpi = clamp_button(x, y, size, mons, size * 3)
    return x, y, button_size(dpi)


def clamp_rect(x, y, width, height):
    vx, vy, vw, vh = capture.virtual_screen()
    x2 = min(x + width, vx + vw)
    y2 = min(y + height, vy + vh)
    x = max(x, vx)
    y = max(y, vy)
    return int(x), int(y), int(x2 - x), int(y2 - y)


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
        self.size = 52
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
        self.bridge = None
        self.setup = None
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("QuickShotResident")
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
        self.root.update_idletasks()
        capture.exclude_window_from_capture(int(self.win.winfo_id()))
        try:
            self.bridge = bridge.Bridge()
            self.extension_dir = self.bridge.start()
        except Exception:
            self.bridge = None
            self.extension_dir = ""

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
        except Exception:
            pass
        if isinstance(saved_x, (int, float)) and isinstance(saved_y, (int, float)):
            mons = capture.monitors()
            size = button_size(monitor_for_point(saved_x, saved_y, mons)[4])
            x, y, dpi = clamp_button(saved_x, saved_y, size, mons, size * 3)
            self.apply_geometry(x, y, button_size(dpi))
        else:
            x, y, size = default_button_origin()
            self.apply_geometry(x, y, size)

    def apply_geometry(self, x, y, size):
        self.size = int(size)
        self.height = self.size * 3
        self.pos = (int(x), int(y))
        self.icon.configure(width=self.size, height=self.height)
        self.win.geometry(f"{self.size}x{self.height}+{self.pos[0]}+{self.pos[1]}")
        self.draw_icon()

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

    def save_settings(self):
        try:
            payload = {"x": self.pos[0], "y": self.pos[1], "lang": self.lang}
            path = settings_path()
            temp = path + ".tmp"
            with open(temp, "w", encoding="utf-8") as handle:
                json.dump(payload, handle)
            os.replace(temp, path)
        except Exception:
            return

    def set_lang(self, lang):
        if lang not in STRINGS:
            return
        self.lang = lang
        self.save_settings()
        self.hide_tip()

    def on_press(self, event):
        if self.busy:
            return "break"
        self.hide_tip()
        self.press = (event.x_root, event.y_root)
        self.origin = (self.win.winfo_x(), self.win.winfo_y())
        self.moved = False
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
            return "break"
        dx = event.x_root - self.press[0]
        dy = event.y_root - self.press[1]
        moved = self.moved
        origin = self.origin
        self.press = None
        self.origin = None
        self.moved = False
        if moved:
            mons = capture.monitors()
            drop_x = origin[0] + dx
            drop_y = origin[1] + dy
            dpi = monitor_for_point(drop_x + self.size / 2, drop_y + self.height / 2, mons)[4]
            size = button_size(dpi)
            x, y, _dpi = clamp_button(drop_x, drop_y, size, mons, size * 3)
            self.apply_geometry(x, y, size)
            self.save_settings()
        else:
            zone = int(event.y // self.size) if self.size else 0
            if zone <= 0:
                self.begin_select()
            elif zone == 1:
                self.capture_screen()
            else:
                self.capture_page()
        return "break"

    def on_right_click(self, event):
        self.hide_tip()
        menu = tk.Menu(self.win, tearoff=0)
        menu.add_command(label=f"QuickShot {VERSION}", state="disabled")
        menu.add_command(label=self.tr("screen"), command=self.capture_screen)
        menu.add_command(label=self.tr("page"), command=self.capture_page)
        menu.add_separator()
        menu.add_command(
            label="日本語 ✓" if self.lang == "ja" else "日本語",
            command=lambda: self.set_lang("ja"),
        )
        menu.add_command(
            label="English ✓" if self.lang == "en" else "English",
            command=lambda: self.set_lang("en"),
        )
        menu.add_separator()
        menu.add_command(label=self.tr("exit"), command=self.quit)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

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
        y = self.win.winfo_y() + self.size + 6
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
        toast.deiconify()
        capture.exclude_window_from_capture(int(toast.winfo_id()))
        self.toast = toast
        self.toast_job = self.root.after(ms, self.close_toast)

    def capture_screen(self):
        if self.busy or self.closing:
            return
        self.busy = True
        try:
            self.close_toast()
            self.hide_button()
            self.root.update()
            path, count, _width, _height = pngsave.save_full_screen()
            self.show_button()
            label = self.tr("saved_one") if count <= 1 else self.tr("saved_many").format(n=count)
            self.show_notice(label + "\n" + path)
        except ValueError:
            self.show_button()
            self.show_notice(self.tr("screen_large"))
        except Exception:
            self.show_button()
            self.show_notice(self.tr("screen_failed"))
        finally:
            self.busy = False

    def capture_page(self):
        if self.busy or self.closing:
            return
        if self.bridge is None or not self.bridge.connected():
            self.show_setup()
            return
        self.busy = True
        self.page_started = time.time()
        self.page_path = None
        self.page_done = False
        self.page_truncated = False
        try:
            self.bridge.request_capture()
        except Exception:
            self.busy = False
            self.show_notice(self.tr("page_failed"))
            return
        self.show_notice(self.tr("page_start"), 30000)
        self.root.after(300, self.poll_page)

    def poll_page(self):
        if not self.busy:
            return
        saved = None
        failed = None
        try:
            messages = self.bridge.take_messages() if self.bridge else []
        except Exception:
            messages = []
        for message in messages:
            kind = message.get("type")
            if kind == "progress" and message.get("text"):
                self.show_notice(str(message["text"]), 30000)
            elif kind == "png":
                try:
                    path = pngsave.unique_png("page")
                    with open(path, "wb") as handle:
                        handle.write(message["data"])
                    saved = path
                    self.page_path = path
                except Exception:
                    failed = self.tr("page_failed")
            elif kind == "error":
                failed = str(message.get("message") or self.tr("page_failed"))
            elif kind == "done":
                self.page_done = True
                self.page_truncated = bool(message.get("truncated"))
        if failed:
            self.busy = False
            self.show_notice(failed)
            return
        if self.page_path and self.page_done:
            self.busy = False
            label = self.tr("page_truncated") if self.page_truncated else self.tr("page_saved")
            self.show_notice(label + "\n" + self.page_path)
            return
        if time.time() - self.page_started > 90:
            self.busy = False
            self.show_notice(self.tr("page_timeout"))
            return
        self.root.after(300, self.poll_page)

    def show_setup(self):
        if self.setup is not None:
            try:
                self.setup.lift()
                return
            except tk.TclError:
                self.setup = None
        folder = self.extension_dir or ""
        if self.lang == "ja":
            text = (
                "ページ全体の撮影には、初回だけ拡張機能の読み込みが必要です。\n"
                "ブラウザは終了も再起動もしません。\n\n"
                "1. QuickShot を起動したまま、Chrome または Edge で拡張機能の管理を開く\n"
                "2. デベロッパーモードをオンにする\n"
                "3. 「パッケージ化されていない拡張機能を読み込む」で次のフォルダを選ぶ\n"
                f"{folder}\n"
                "4. すでに読み込んでいる場合は、その拡張機能を再読み込みする\n"
                "5. 撮影したい http(s) のページを表示し、下のボタンを押す\n\n"
                "chrome:// のページや、拡張機能が未接続のときは撮影できません。"
            )
        else:
            text = (
                "Full-page capture needs the extension loaded once.\n"
                "QuickShot does not close or restart the browser.\n\n"
                "1. Keep QuickShot running and open the extensions page in Chrome or Edge\n"
                "2. Turn on Developer mode\n"
                "3. Choose Load unpacked and select this folder\n"
                f"{folder}\n"
                "4. If it is already loaded, reload that extension\n"
                "5. Open the http(s) page and press the bottom button\n\n"
                "chrome:// pages cannot be captured, and capture fails until the extension is connected."
            )
        window = tk.Toplevel(self.root)
        window.title(self.tr("page_setup_title"))
        window.configure(bg="white")
        window.geometry("520x360")
        tk.Label(window, text=text, bg="white", justify="left", wraplength=480, padx=16, pady=16).pack(fill="both", expand=True)
        self.setup = window
        window.protocol("WM_DELETE_WINDOW", self.close_setup)

    def close_setup(self):
        if self.setup is not None:
            try:
                self.setup.destroy()
            except tk.TclError:
                pass
            self.setup = None

    def hide_button(self):
        self.hide_tip()
        self.win.withdraw()
        self.root.update()

    def show_button(self):
        self.win.deiconify()
        self.win.attributes("-topmost", True)
        self.win.lift()
        self.root.update_idletasks()

    def begin_select(self):
        if self.busy or self.closing:
            return
        self.busy = True
        try:
            self.close_toast()
            self.hide_button()
            self.open_overlay()
        except Exception:
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
            if rect is not None:
                x, y, width, height = clamp_rect(rect[0], rect[1], rect[2], rect[3])
                if width >= 3 and height >= 3:
                    self.pump(0.12)
                    capture.copy_dib_to_clipboard(capture.capture_region(x, y, width, height))
                    copied = True
        except Exception:
            failed = True
        finally:
            self.destroy_overlay()
            self.show_button()
            self.closing = False
            if failed:
                self.show_toast("failed")
            elif copied:
                self.show_toast("copied")

    def quit(self):
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
        lang = peek_lang()
        capture.user32.MessageBoxW(
            None,
            STRINGS[lang]["already"],
            "QuickShot",
            0x00000040 | 0x00010000 | 0x00040000,
        )
        return 2
    try:
        App().run()
    except Exception as exc:
        capture.user32.MessageBoxW(None, str(exc)[:500], "QuickShot", 0x00000010)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
