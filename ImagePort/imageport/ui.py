from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from imageport import __version__
from imageport.dropfiles import enable_file_drop, take_dropped
from imageport.errors import ImagePortError
from imageport.formats import OUTPUT_FORMATS, input_kind
from imageport.pipeline import Converted, convert_file
from imageport.save import NameAllocator
from imageport.settings import RESIZE_CHOICES, load_settings, save_settings

FORMAT_LABELS = [("auto", "おまかせ圧縮")] + [
    (key, spec.label) for key, spec in OUTPUT_FORMATS.items()
]
RESIZE_LABELS = [
    ("none", "そのまま"),
    ("1920", "長辺 1920"),
    ("1280", "長辺 1280"),
    ("800", "長辺 800"),
]


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / 1024 / 1024:.2f} MB"


def reduction_text(before: int, after: int) -> str:
    if before <= 0:
        return "-"
    percent = (before - after) / before * 100
    if percent >= 0:
        return f"{percent:.0f}% 削減"
    return f"{-percent:.0f}% 増加"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.files: list[Path] = []
        self.messages: queue.Queue = queue.Queue()
        self.output_dirs: list[Path] = []
        self.running = False
        self.settings = load_settings()
        root.title(f"ImagePort {__version__}")
        root.minsize(560, 520)
        root.geometry("760x640")
        root.configure(bg="#ffffff")
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Primary.TButton", font=("Yu Gothic UI", 12, "bold"))
        self._build()
        root.after(200, self._enable_drop)
        root.after(100, self._poll)
        root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ImagePort", font=("Yu Gothic UI", 20, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text="画像を入れて、変換するを押してください。元の画像はそのまま残ります。",
            font=("Yu Gothic UI", 10),
        ).pack(anchor="w", pady=(2, 10))

        self.drop = tk.Label(
            outer,
            text="ここに画像をドロップ",
            bg="#f4f7fb",
            fg="#1d4ed8",
            relief="solid",
            bd=1,
            padx=12,
            pady=28,
            font=("Yu Gothic UI", 12),
        )
        self.drop.pack(fill="x")

        picker = ttk.Frame(outer)
        picker.pack(fill="x", pady=(8, 0))
        ttk.Button(picker, text="画像を選ぶ", command=self._pick).pack(side="left")
        ttk.Button(picker, text="一覧をクリア", command=self._clear).pack(side="left", padx=(8, 0))
        self.count_label = ttk.Label(picker, text="0件")
        self.count_label.pack(side="right")

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=12)
        ttk.Label(options, text="出力形式").grid(row=0, column=0, sticky="w")
        self.format_var = tk.StringVar(value=self._label_for(FORMAT_LABELS, self.settings["output_format"]))
        ttk.Combobox(
            options,
            textvariable=self.format_var,
            values=[label for _, label in FORMAT_LABELS],
            state="readonly",
            width=18,
        ).grid(row=0, column=1, padx=(8, 16))
        ttk.Label(options, text="リサイズ").grid(row=0, column=2, sticky="w")
        self.resize_var = tk.StringVar(value=self._label_for(RESIZE_LABELS, self.settings["resize"]))
        ttk.Combobox(
            options,
            textvariable=self.resize_var,
            values=[label for _, label in RESIZE_LABELS],
            state="readonly",
            width=14,
        ).grid(row=0, column=3, padx=(8, 0))
        ttk.Label(options, text="小さい画像は拡大しません").grid(row=1, column=2, columnspan=2, sticky="w", pady=(4, 0))

        self.convert_button = ttk.Button(outer, text="変換する", style="Primary.TButton", command=self._start)
        self.convert_button.pack(fill="x", pady=(0, 8))
        self.progress = ttk.Label(outer, text="待機中")
        self.progress.pack(anchor="w")

        columns = ("name", "before", "after", "result")
        self.tree = ttk.Treeview(outer, columns=columns, show="headings", height=10)
        for key, heading, width in (
            ("name", "ファイル", 280),
            ("before", "変換前", 90),
            ("after", "変換後", 90),
            ("result", "結果", 110),
        ):
            self.tree.heading(key, text=heading)
            self.tree.column(key, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(6, 6))

        self.error_box = tk.Text(outer, height=4, wrap="word", relief="flat", bg="#f8fafc")
        self.error_box.pack(fill="x")
        self.error_box.configure(state="disabled")
        self.open_button = ttk.Button(outer, text="保存フォルダを開く", command=self._open_folder, state="disabled")
        self.open_button.pack(anchor="w", pady=(8, 0))

    def _enable_drop(self) -> None:
        try:
            enable_file_drop(self.root)
        except Exception:
            self._write_error("ドラッグ＆ドロップを開始できませんでした。画像を選ぶから追加できます。")

    def _label_for(self, pairs, key: str) -> str:
        for item_key, label in pairs:
            if item_key == key:
                return label
        return pairs[0][1]

    def _key_for(self, pairs, label: str) -> str:
        for item_key, item_label in pairs:
            if item_label == label:
                return item_key
        return pairs[0][0]

    def _pick(self) -> None:
        names = filedialog.askopenfilenames(
            title="画像を選ぶ",
            filetypes=[("画像", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif *.ico"), ("すべて", "*.*")],
        )
        if names:
            self.add_paths(list(names))

    def add_paths(self, paths: list[str]) -> None:
        for raw in paths:
            path = Path(raw)
            if path.is_dir():
                children = [child for child in path.iterdir() if child.is_file()]
                self.add_paths([str(child) for child in children])
                continue
            kind = input_kind(path.suffix)
            if kind != "supported":
                if kind == "future":
                    self._write_error(f"{path.name}: この形式は現在のバージョンでは未対応です")
                else:
                    self._write_error(f"{path.name}: 未対応の形式です")
                continue
            if path not in self.files:
                self.files.append(path)
        self.count_label.configure(text=f"{len(self.files)}件")

    def _clear(self) -> None:
        if self.running:
            return
        self.files.clear()
        self.output_dirs.clear()
        self.count_label.configure(text="0件")
        self.tree.delete(*self.tree.get_children())
        self._set_errors("")
        self.progress.configure(text="待機中")
        self.open_button.configure(state="disabled")

    def _start(self) -> None:
        if self.running or not self.files:
            if not self.files:
                self.progress.configure(text="画像を追加してください")
            return
        output_format = self._key_for(FORMAT_LABELS, self.format_var.get())
        resize = self._key_for(RESIZE_LABELS, self.resize_var.get())
        save_settings({"output_format": output_format, "resize": resize})
        self.running = True
        self.convert_button.configure(state="disabled")
        self.tree.delete(*self.tree.get_children())
        self._set_errors("")
        self.output_dirs.clear()
        paths = list(self.files)
        threading.Thread(
            target=self._worker,
            args=(paths, output_format, RESIZE_CHOICES[resize]),
            daemon=True,
        ).start()

    def _worker(self, paths: list[Path], output_format: str, max_edge: int | None) -> None:
        names = NameAllocator()
        total = len(paths)
        for index, path in enumerate(paths, start=1):
            try:
                result = convert_file(path, output_format, max_edge, names)
            except ImagePortError as exc:
                result = exc
            except Exception:
                result = ImagePortError("変換に失敗しました")
            self.messages.put((index, total, path, result))
        self.messages.put(None)

    def _poll(self) -> None:
        for paths in take_dropped():
            if paths:
                self.add_paths(paths)
        while True:
            try:
                item = self.messages.get_nowait()
            except queue.Empty:
                break
            if item is None:
                self.running = False
                self.convert_button.configure(state="normal")
                self.progress.configure(text="完了")
                continue
            index, total, path, result = item
            self.progress.configure(text=f"{index} / {total} 件")
            if isinstance(result, Converted):
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        path.name,
                        format_size(result.before),
                        format_size(result.after),
                        reduction_text(result.before, result.after),
                    ),
                )
                folder = result.output.parent
                if folder not in self.output_dirs:
                    self.output_dirs.append(folder)
                self.open_button.configure(state="normal")
            else:
                message = str(result) if isinstance(result, ImagePortError) else "変換に失敗しました"
                self._write_error(f"{path.name}: {message}")
                self.tree.insert("", "end", values=(path.name, "-", "-", "失敗"))
        self.root.after(100, self._poll)

    def _write_error(self, text: str) -> None:
        self.error_box.configure(state="normal")
        current = self.error_box.get("1.0", "end").strip()
        self.error_box.insert("end", (("\n" if current else "") + text))
        self.error_box.configure(state="disabled")

    def _set_errors(self, text: str) -> None:
        self.error_box.configure(state="normal")
        self.error_box.delete("1.0", "end")
        if text:
            self.error_box.insert("end", text)
        self.error_box.configure(state="disabled")

    def _open_folder(self) -> None:
        if not self.output_dirs:
            return
        import os

        os.startfile(self.output_dirs[-1])

    def _close(self) -> None:
        output_format = self._key_for(FORMAT_LABELS, self.format_var.get())
        resize = self._key_for(RESIZE_LABELS, self.resize_var.get())
        save_settings({"output_format": output_format, "resize": resize})
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
