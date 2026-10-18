"""Accept files dropped onto a Tk window. Windows only."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

shell32 = ctypes.windll.shell32
user32 = ctypes.windll.user32

WM_DROPFILES = 0x0233
GWLP_WNDPROC = -4

LRESULT = ctypes.c_ssize_t
user32.CallWindowProcW.argtypes = [
    ctypes.c_void_p,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.CallWindowProcW.restype = LRESULT
user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
user32.SetWindowLongPtrW.restype = ctypes.c_void_p
user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = ctypes.c_void_p
shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
shell32.DragQueryFileW.argtypes = [
    wintypes.HANDLE,
    wintypes.UINT,
    ctypes.c_wchar_p,
    wintypes.UINT,
]
shell32.DragQueryFileW.restype = wintypes.UINT
shell32.DragFinish.argtypes = [wintypes.HANDLE]

WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# Filled only from the window procedure. The UI thread drains it.
# Do not call Tk here: a drop arrives while Tk has released the GIL, and
# touching Tk from this callback aborts the process.
_pending: list[list[str]] = []


def take_dropped() -> list[list[str]]:
    if not _pending:
        return []
    items = list(_pending)
    _pending.clear()
    return items


def enable_file_drop(widget) -> None:
    widget.update_idletasks()
    hwnd = wintypes.HWND(widget.winfo_id())
    shell32.DragAcceptFiles(hwnd, True)
    old_proc = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)

    def window_proc(hwnd_value, msg, wparam, lparam):
        if msg == WM_DROPFILES:
            try:
                _pending.append(_dropped_paths(wparam))
            except Exception:
                _pending.append([])
            return 0
        return user32.CallWindowProcW(old_proc, hwnd_value, msg, wparam, lparam)

    proc = WNDPROC(window_proc)
    widget._imageport_drop_proc = proc
    user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.cast(proc, ctypes.c_void_p))


def _dropped_paths(handle) -> list[str]:
    count = shell32.DragQueryFileW(handle, 0xFFFFFFFF, None, 0)
    paths = []
    for index in range(count):
        length = shell32.DragQueryFileW(handle, index, None, 0)
        buffer = ctypes.create_unicode_buffer(length + 1)
        shell32.DragQueryFileW(handle, index, buffer, length + 1)
        if buffer.value:
            paths.append(buffer.value)
    shell32.DragFinish(handle)
    return paths
