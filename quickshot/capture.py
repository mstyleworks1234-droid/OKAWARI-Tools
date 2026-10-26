"""Screen capture and clipboard copy via Win32 GDI.

Images stay in memory. This module does not write files or use the network.
"""

import ctypes
from ctypes import wintypes
import time

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

try:
    shcore = ctypes.WinDLL("shcore", use_last_error=True)
except OSError:
    shcore = None

SRCCOPY = 0x00CC0020
CAPTUREBLT = 0x40000000
BI_RGB = 0
DIB_RGB_COLORS = 0
CF_DIB = 8
GMEM_MOVEABLE = 0x0002
ERROR_ALREADY_EXISTS = 183
WDA_EXCLUDEFROMCAPTURE = 0x00000011
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


MONITORENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    wintypes.HMONITOR,
    wintypes.HDC,
    ctypes.POINTER(wintypes.RECT),
    wintypes.LPARAM,
)

user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL
user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user32.SetProcessDPIAware.restype = wintypes.BOOL
user32.GetSystemMetrics.restype = ctypes.c_int
user32.GetSystemMetrics.argtypes = [ctypes.c_int]
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = [wintypes.HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.OpenClipboard.restype = wintypes.BOOL
user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.EmptyClipboard.restype = wintypes.BOOL
user32.CloseClipboard.restype = wintypes.BOOL
user32.SetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.EnumDisplayMonitors.restype = wintypes.BOOL
user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, MONITORENUMPROC, wintypes.LPARAM]
user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.GetParent.restype = wintypes.HWND
user32.GetParent.argtypes = [wintypes.HWND]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]

user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
user32.MessageBoxW.restype = ctypes.c_int
user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]

gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.BitBlt.restype = wintypes.BOOL
gdi32.BitBlt.argtypes = [
    wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HDC, ctypes.c_int, ctypes.c_int, wintypes.DWORD,
]
gdi32.GetDIBits.restype = ctypes.c_int
gdi32.GetDIBits.argtypes = [
    wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT,
    ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT,
]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]

kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalFree.restype = wintypes.HGLOBAL
kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
kernel32.GetUserDefaultUILanguage.restype = wintypes.WORD

if shcore is not None:
    shcore.SetProcessDpiAwareness.restype = ctypes.HRESULT
    shcore.SetProcessDpiAwareness.argtypes = [ctypes.c_int]
    shcore.GetDpiForMonitor.restype = ctypes.HRESULT
    shcore.GetDpiForMonitor.argtypes = [
        wintypes.HMONITOR, ctypes.c_int,
        ctypes.POINTER(wintypes.UINT), ctypes.POINTER(wintypes.UINT),
    ]

_mutex_handle = None


def enable_dpi_awareness():
    """Call before any window is created so capture keeps physical pixels."""
    try:
        if user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            return
    except Exception:
        pass
    if shcore is not None:
        try:
            if shcore.SetProcessDpiAwareness(2) == 0:
                return
        except Exception:
            pass
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass


def windows_ui_lang():
    langid = int(kernel32.GetUserDefaultUILanguage() or 0)
    if (langid & 0x3FF) == 0x11:
        return "ja"
    return "en"


def virtual_screen():
    x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    if w <= 0 or h <= 0:
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        x, y = 0, 0
    return int(x), int(y), int(w), int(h)


def monitors():
    """Return (left, top, right, bottom, dpi, work_left, work_top, work_right, work_bottom)."""
    found = []

    @MONITORENUMPROC
    def _callback(hmon, _hdc, rect, _data):
        box = rect.contents
        dpi = 96
        if shcore is not None:
            dpi_x = wintypes.UINT()
            dpi_y = wintypes.UINT()
            if shcore.GetDpiForMonitor(hmon, 0, ctypes.byref(dpi_x), ctypes.byref(dpi_y)) == 0:
                dpi = int(dpi_x.value) or 96
        work = (int(box.left), int(box.top), int(box.right), int(box.bottom))
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(hmon, ctypes.byref(info)):
            area = info.rcWork
            work = (int(area.left), int(area.top), int(area.right), int(area.bottom))
        found.append((int(box.left), int(box.top), int(box.right), int(box.bottom), dpi, *work))
        return 1

    if not user32.EnumDisplayMonitors(None, None, _callback, 0) or not found:
        x, y, w, h = virtual_screen()
        return [(x, y, x + w, y + h, 96, x, y, x + w, y + h)]
    return found


def acquire_single_instance():
    """Return False when another QuickShot process already holds the mutex."""
    global _mutex_handle
    ctypes.set_last_error(0)
    handle = kernel32.CreateMutexW(None, False, "Local\\OKAWARI.QuickShot.SingleInstance")
    err = ctypes.get_last_error()
    if not handle:
        return True
    if err == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False
    _mutex_handle = handle
    return True


def hold_topmost(hwnd, enabled):
    """Keep a window above normal apps without activating it."""
    if not hwnd:
        return False
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, ctypes.c_void_p,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT,
    ]
    insert = ctypes.c_void_p(-1 if enabled else -2)
    return bool(user32.SetWindowPos(int(hwnd), insert, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010))


class _NotifyIcon(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
    ]


_shell32 = ctypes.WinDLL("shell32", use_last_error=True)
_shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(_NotifyIcon)]
_shell32.Shell_NotifyIconW.restype = wintypes.BOOL
user32.LoadIconW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
user32.LoadIconW.restype = wintypes.HICON
_tray = None


def tray_add(hwnd):
    """Show a notification icon for this GUI process. It does not start a new process."""
    global _tray
    if not hwnd:
        return False
    icon = user32.LoadIconW(None, ctypes.c_void_p(32512))
    data = _NotifyIcon()
    data.cbSize = ctypes.sizeof(_NotifyIcon)
    data.hWnd = int(hwnd)
    data.uID = 1
    data.uFlags = 2 | 4
    data.hIcon = icon
    data.szTip = "QuickShot"
    if not _shell32.Shell_NotifyIconW(0, ctypes.byref(data)):
        return False
    _tray = data
    return True


def tray_remove():
    global _tray
    if _tray is None:
        return False
    removed = bool(_shell32.Shell_NotifyIconW(2, ctypes.byref(_tray)))
    _tray = None
    return removed


def exclude_window_from_capture(hwnd):
    """Ask DWM to leave this window out of screenshots. Best-effort."""
    if not hwnd:
        return False
    if user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE):
        return True
    parent = user32.GetParent(hwnd)
    if parent and user32.SetWindowDisplayAffinity(parent, WDA_EXCLUDEFROMCAPTURE):
        return True
    return False


def _row_stride(width):
    return ((width * 3 + 3) // 4) * 4


def capture_region(x, y, width, height):
    """Return a 24-bit CF_DIB (header + bottom-up BGR) for the screen rectangle."""
    x, y, width, height = int(x), int(y), int(width), int(height)
    if width < 1 or height < 1:
        raise ValueError("empty region")
    if width > 20000 or height > 20000:
        raise ValueError("region too large")

    stride = _row_stride(width)
    image_size = stride * height
    screen = user32.GetDC(0)
    if not screen:
        raise OSError("GetDC failed")
    memory = None
    bitmap = None
    selected = None
    try:
        memory = gdi32.CreateCompatibleDC(screen)
        if not memory:
            raise OSError("CreateCompatibleDC failed")
        bitmap = gdi32.CreateCompatibleBitmap(screen, width, height)
        if not bitmap:
            raise OSError("CreateCompatibleBitmap failed")
        selected = gdi32.SelectObject(memory, bitmap)
        if not gdi32.BitBlt(memory, 0, 0, width, height, screen, x, y, SRCCOPY | CAPTUREBLT):
            raise OSError("BitBlt failed")
        gdi32.SelectObject(memory, selected)
        selected = None

        header = BITMAPINFOHEADER()
        header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        header.biWidth = width
        header.biHeight = height
        header.biPlanes = 1
        header.biBitCount = 24
        header.biCompression = BI_RGB
        header.biSizeImage = image_size
        pixels = ctypes.create_string_buffer(image_size)
        lines = gdi32.GetDIBits(
            memory, bitmap, 0, height, pixels, ctypes.byref(header), DIB_RGB_COLORS
        )
        if lines != height:
            raise OSError("GetDIBits failed")

        header.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        header.biWidth = width
        header.biHeight = height
        header.biPlanes = 1
        header.biBitCount = 24
        header.biCompression = BI_RGB
        header.biSizeImage = image_size
        header.biXPelsPerMeter = 0
        header.biYPelsPerMeter = 0
        header.biClrUsed = 0
        header.biClrImportant = 0
        return bytes(header) + pixels.raw
    finally:
        if selected and memory:
            gdi32.SelectObject(memory, selected)
        if bitmap:
            gdi32.DeleteObject(bitmap)
        if memory:
            gdi32.DeleteDC(memory)
        user32.ReleaseDC(0, screen)


def copy_dib_to_clipboard(dib):
    if not dib:
        raise ValueError("empty dib")
    opened = False
    for _ in range(8):
        if user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(0.03)
    if not opened:
        raise OSError("OpenClipboard failed")
    allocated = None
    try:
        if not user32.EmptyClipboard():
            raise OSError("EmptyClipboard failed")
        allocated = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib))
        if not allocated:
            raise OSError("GlobalAlloc failed")
        pointer = kernel32.GlobalLock(allocated)
        if not pointer:
            raise OSError("GlobalLock failed")
        ctypes.memmove(pointer, dib, len(dib))
        kernel32.GlobalUnlock(allocated)
        if not user32.SetClipboardData(CF_DIB, allocated):
            raise OSError("SetClipboardData failed")
        allocated = None
    finally:
        if allocated:
            kernel32.GlobalFree(allocated)
        user32.CloseClipboard()
