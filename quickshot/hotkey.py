"""Global Ctrl+Shift+1/2/3 hotkeys. They do not activate QuickShot."""

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001
_KEYS = ((1, 0x31), (2, 0x32), (3, 0x33))


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt_x", wintypes.LONG),
        ("pt_y", wintypes.LONG),
    ]


user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.PeekMessageW.argtypes = [
    ctypes.POINTER(_MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT,
]
user32.PeekMessageW.restype = wintypes.BOOL


def register():
    mods = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
    failed = []
    for ident, vk in _KEYS:
        if not user32.RegisterHotKey(None, ident, mods, vk):
            failed.append(ident)
    return failed


def poll():
    found = []
    message = _MSG()
    while user32.PeekMessageW(ctypes.byref(message), None, WM_HOTKEY, WM_HOTKEY, PM_REMOVE):
        found.append(int(message.wParam))
    return found


def unregister():
    for ident, _vk in _KEYS:
        user32.UnregisterHotKey(None, ident)
