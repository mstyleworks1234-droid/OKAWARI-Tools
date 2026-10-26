"""Small separate editor. The original PNG is not overwritten."""

import os
import tempfile
import tkinter as tk
from tkinter import filedialog

import imageutil


def open_editor(parent, path, tr, on_close=None):
    if not path or not os.path.isfile(path):
        return None
    try:
        width, height = imageutil.dimensions(path)
    except Exception:
        return None
    if width * height > 40000000:
        return "large"
    window = tk.Toplevel(parent)
    window.title("QuickShot")
    window.geometry("980x640")
    window.attributes("-topmost", True)
    state = {
        "ops": [],
        "tool": tk.StringVar(value="crop"),
        "edge": 1100,
        "scale": 1.0,
        "start": None,
        "rubber": None,
        "photo": None,
        "preview": None,
    }
    fit = min(1.0, 900.0 / max(width, 1))
    state["edge"] = max(1, int(round(max(width, height) * fit)))
    bar = tk.Frame(window)
    bar.pack(fill="x", padx=8, pady=6)
    tools = (
        ("crop", "crop"),
        ("mosaic", "mosaic"),
    )
    buttons = {}
    for key, value in tools:
        button = tk.Radiobutton(bar, text=tr(key), variable=state["tool"], value=value, indicatoron=False)
        button.pack(side="left", padx=2)
        buttons[key] = button
    tk.Button(bar, text="-", command=lambda: zoom(0.8)).pack(side="left", padx=(12, 2))
    tk.Button(bar, text="+", command=lambda: zoom(1.25)).pack(side="left", padx=2)
    undo_button = tk.Button(bar, text=tr("undo"), command=lambda: undo())
    undo_button.pack(side="left", padx=(12, 2))
    save_button = tk.Button(bar, text=tr("save_as"), command=lambda: save_as())
    save_button.pack(side="left", padx=2)
    copy_button = tk.Button(bar, text=tr("copy_button"), command=lambda: copy_image())
    copy_button.pack(side="left", padx=2)
    hint = tk.Label(window, anchor="w", fg="#374151", text=tr("edit_hint"))
    hint.pack(fill="x", padx=8)
    status = tk.Label(window, anchor="w")
    status.pack(fill="x", padx=8)
    body = tk.Frame(window)
    body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    yscroll = tk.Scrollbar(body, orient="vertical")
    xscroll = tk.Scrollbar(body, orient="horizontal")
    canvas = tk.Canvas(
        body, bg="#e5e7eb", highlightthickness=0,
        xscrollcommand=xscroll.set, yscrollcommand=yscroll.set,
    )
    yscroll.config(command=canvas.yview)
    xscroll.config(command=canvas.xview)
    yscroll.pack(side="right", fill="y")
    xscroll.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    def origin():
        for op in state["ops"]:
            if op.get("t") == "crop":
                return float(op["x"]), float(op["y"])
        return 0.0, 0.0

    def image_point(x, y):
        ox, oy = origin()
        scale = state["scale"] or 1
        return ox + x / scale, oy + y / scale

    def redraw():
        dest = state["preview"]
        if not dest:
            handle = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            handle.close()
            dest = handle.name
            state["preview"] = dest
        try:
            _out_w, _out_h, scale = imageutil.render(path, state["ops"], dest, state["edge"])
        except ValueError:
            status.configure(text=tr("edit_large"))
            canvas.delete("all")
            canvas.create_text(16, 16, anchor="nw", fill="#991b1b", text=tr("edit_large"))
            return
        except Exception as exc:
            message = str(exc)[:180] or tr("edit_large")
            status.configure(text=message)
            canvas.delete("all")
            canvas.create_text(16, 16, anchor="nw", fill="#991b1b", text=message)
            return
        state["scale"] = scale or 1
        try:
            state["photo"] = tk.PhotoImage(file=dest)
        except tk.TclError as exc:
            status.configure(text=str(exc)[:180])
            canvas.delete("all")
            canvas.create_text(16, 16, anchor="nw", fill="#991b1b", text=str(exc)[:180])
            return
        canvas.delete("all")
        canvas.configure(scrollregion=(0, 0, state["photo"].width(), state["photo"].height()))
        canvas.create_image(0, 0, anchor="nw", image=state["photo"])
        status.configure(text="%s  %s×%s" % (os.path.basename(path), width, height))

    def zoom(factor):
        nxt = max(200, int(state["edge"] * factor))
        preview = nxt / max(width, height, 1)
        if preview * preview * width * height > 30_000_000:
            return
        state["edge"] = nxt
        redraw()

    def undo():
        if state["ops"]:
            state["ops"].pop()
            redraw()

    def save_as():
        dest = filedialog.asksaveasfilename(
            parent=window,
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            title=tr("save_as"),
        )
        if not dest:
            return
        if os.path.abspath(dest) == os.path.abspath(path):
            status.configure(text=tr("edit_keep"))
            return
        try:
            imageutil.render(path, state["ops"], dest, 0)
        except ValueError:
            status.configure(text=tr("edit_large"))
            return
        except Exception as exc:
            status.configure(text=str(exc)[:180])
            return
        status.configure(text=tr("edit_saved") + "\n" + dest)

    def copy_image():
        dest = os.path.join(tempfile.gettempdir(), "QuickShot-edit-copy.png")
        try:
            imageutil.render(path, state["ops"], dest, 0)
            imageutil.copy_png_file(dest)
            status.configure(text=tr("copied"))
        except Exception as exc:
            status.configure(text=str(exc)[:180])

    def on_down(event):
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        state["start"] = (x, y)
        if state["rubber"]:
            canvas.delete(state["rubber"])
        state["rubber"] = canvas.create_rectangle(x, y, x, y, outline="#111827")

    def on_move(event):
        if not state["start"] or not state["rubber"]:
            return
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        x1, y1 = state["start"]
        canvas.coords(state["rubber"], x1, y1, x, y)

    def on_wheel(event):
        canvas.yview_scroll(int(-event.delta / 120), "units")

    def on_up(event):
        if not state["start"]:
            return
        x1, y1 = state["start"]
        state["start"] = None
        if state["rubber"]:
            canvas.delete(state["rubber"])
            state["rubber"] = None
        x2, y2 = canvas.canvasx(event.x), canvas.canvasy(event.y)
        ax, ay = image_point(x1, y1)
        bx, by = image_point(x2, y2)
        left, top = min(ax, bx), min(ay, by)
        wide, high = abs(bx - ax), abs(by - ay)
        tool = state["tool"].get()
        if wide < 3 or high < 3:
            return
        if tool == "crop":
            state["ops"] = [op for op in state["ops"] if op.get("t") != "crop"]
            state["ops"].insert(0, {"t": "crop", "x": left, "y": top, "w": wide, "h": high})
        elif tool == "mosaic":
            state["ops"].append({"t": "mosaic", "x": left, "y": top, "w": wide, "h": high})
        redraw()

    canvas.bind("<ButtonPress-1>", on_down)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_up)
    canvas.bind("<MouseWheel>", on_wheel)

    def close():
        try:
            if on_close:
                on_close()
        finally:
            window.destroy()

    window.protocol("WM_DELETE_WINDOW", close)

    def refresh_labels():
        for key, button in buttons.items():
            button.configure(text=tr(key))
        hint.configure(text=tr("edit_hint"))
        undo_button.configure(text=tr("undo"))
        save_button.configure(text=tr("save_as"))
        copy_button.configure(text=tr("copy_button"))

    window.refresh_labels = refresh_labels
    redraw()
    return window
