"""Windows destination guards and Unicode input. Normal typing never touches the clipboard."""

import ctypes as C
import logging
import time
from ctypes import wintypes as W

LOG = logging.getLogger(__name__)
# Keyboard keys only. Pressing one during a hold means another shortcut (for
# example Ctrl+Alt+Delete), so the hold cancels. Mouse buttons do not cancel.
KEYBOARD_KEYS = (
    8,
    9,
    13,
    0x1B,
    32,
    0x21,
    0x22,
    0x23,
    0x24,
    0x25,
    0x26,
    0x27,
    0x28,
    0x2E,
    *range(0x30, 0x5B),
    *range(0x60, 0x70),
    *range(0x70, 0x88),
    *range(0xBA, 0xE3),
)

user32 = C.WinDLL("user32", use_last_error=True)
kernel32 = C.WinDLL("kernel32", use_last_error=True)
user32.GetForegroundWindow.restype = W.HWND
user32.GetParent.argtypes = [W.HWND]
user32.GetParent.restype = W.HWND
user32.GetWindowThreadProcessId.argtypes = [W.HWND, C.POINTER(W.DWORD)]
user32.GetWindowThreadProcessId.restype = W.DWORD
user32.GetAsyncKeyState.argtypes = [C.c_int]
user32.GetAsyncKeyState.restype = C.c_short
kernel32.CreateMutexW.argtypes = [C.c_void_p, W.BOOL, W.LPCWSTR]
kernel32.CreateMutexW.restype = W.HANDLE
kernel32.CloseHandle.argtypes = [W.HANDLE]
kernel32.CreateEventW.argtypes = [C.c_void_p, W.BOOL, W.BOOL, W.LPCWSTR]
kernel32.CreateEventW.restype = W.HANDLE
kernel32.SetEvent.argtypes = [W.HANDLE]
kernel32.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
kernel32.WaitForSingleObject.restype = W.DWORD


class GUIINFO(C.Structure):
    _fields_ = [
        ("cbSize", W.DWORD),
        ("flags", W.DWORD),
        ("hwndActive", W.HWND),
        ("hwndFocus", W.HWND),
        ("hwndCapture", W.HWND),
        ("hwndMenuOwner", W.HWND),
        ("hwndMoveSize", W.HWND),
        ("hwndCaret", W.HWND),
        ("rcCaret", W.RECT),
    ]


user32.GetGUIThreadInfo.argtypes = [W.DWORD, C.POINTER(GUIINFO)]
user32.GetGUIThreadInfo.restype = W.BOOL


class KEYBOARD(C.Structure):
    _fields_ = [
        ("wVk", W.WORD),
        ("wScan", W.WORD),
        ("dwFlags", W.DWORD),
        ("time", W.DWORD),
        ("dwExtraInfo", C.c_size_t),
    ]


class MOUSE(C.Structure):
    _fields_ = [
        ("dx", W.LONG),
        ("dy", W.LONG),
        ("mouseData", W.DWORD),
        ("dwFlags", W.DWORD),
        ("time", W.DWORD),
        ("dwExtraInfo", C.c_size_t),
    ]


class PAYLOAD(C.Union):
    _fields_ = [("ki", KEYBOARD), ("mi", MOUSE)]


class INPUT(C.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", W.DWORD), ("data", PAYLOAD)]


user32.SendInput.argtypes = [W.UINT, C.POINTER(INPUT), C.c_int]
user32.SendInput.restype = W.UINT


def down(key):
    return bool(user32.GetAsyncKeyState(key) & 0x8000)


def modifiers_down():
    return any(down(k) for k in (0x10, 0x11, 0x12, 0x5B, 0x5C))


def target():
    """The foreground window. Dictate's proven check: compare the top-level window
    only. Inner focus handles change inside browsers and Electron apps without the
    destination changing, which made the earlier check save instead of type."""
    hwnd = user32.GetForegroundWindow()
    return int(hwnd) if hwnd else None


def in_menu_mode(hwnd):
    thread = user32.GetWindowThreadProcessId(hwnd, None)
    info = GUIINFO(cbSize=C.sizeof(GUIINFO))
    return bool(user32.GetGUIThreadInfo(thread, C.byref(info)) and info.flags & 0x4)


MENU_MASK_KEY = 0xE8  # unassigned virtual-key code; the same mask AutoHotkey uses


def mask_menu_key():
    """Stop a held Alt or Windows key from opening a menu when it is released.

    Windows opens the app's menu bar (Alt) or Start (Windows) when that key goes
    up with no other key pressed since it went down. One press of an unassigned
    key code breaks that sequence. It is not a modifier and no app acts on it.
    """
    events = (INPUT * 2)(
        INPUT(type=1, ki=KEYBOARD(wVk=MENU_MASK_KEY)),
        INPUT(type=1, ki=KEYBOARD(wVk=MENU_MASK_KEY, dwFlags=2)),
    )
    return user32.SendInput(2, events, C.sizeof(INPUT)) == 2


def insert(text, original, unchanged=lambda: True, waiting=lambda: None):
    """Stop on focus change/modifier use; never steal focus or paste."""
    deadline = time.monotonic() + 5
    if modifiers_down():
        waiting()
    while modifiers_down() and time.monotonic() < deadline:
        if not unchanged():
            return "saved: cancelled or destination changed"
        if target() != original:
            return "saved: focus changed"
        time.sleep(0.02)
    current = target()
    if not original or current != original:
        LOG.warning("Insertion blocked: focus original=%s current=%s", original, current)
        return "saved: focus changed"
    if modifiers_down():
        keys = [hex(key) for key in (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C) if down(key)]
        LOG.warning("Insertion blocked: modifier keys still held=%s", keys)
        return "saved: release shortcut keys"
    if not unchanged():
        return "saved: cancelled or destination changed"
    if in_menu_mode(original):
        # Characters typed into an open menu become menu commands.
        return "saved: app menu was open"
    if not text:
        return "empty"
    delivered = False
    for character in text:
        if target() != original or not unchanged() or modifiers_down():
            return "saved: partial input; check destination" if delivered else "saved: focus or keys changed"
        # Modern Notepad loses Unicode characters when an entire phrase is queued
        # at once. Let the receiving app process each character; keep both UTF-16
        # surrogate units together so emoji remain intact.
        units = character.encode("utf-16-le")
        events = []
        for pos in range(0, len(units), 2):
            unit = int.from_bytes(units[pos : pos + 2], "little")
            events.extend(
                [
                    INPUT(type=1, ki=KEYBOARD(wScan=unit, dwFlags=4)),
                    INPUT(type=1, ki=KEYBOARD(wScan=unit, dwFlags=6)),
                ]
            )
        count = len(events)
        sent = user32.SendInput(count, (INPUT * count)(*events), C.sizeof(INPUT))
        if sent != count:
            return (
                "saved: partial input; check destination"
                if delivered or sent
                else "saved: Windows blocked input"
            )
        delivered = True
        time.sleep(0.01)
    return "typed"


class Instance:
    def __init__(self, name="Local\\SilentType"):
        self.handle = kernel32.CreateMutexW(None, False, name)
        self.exists = C.get_last_error() == 183
        if not self.handle:
            raise C.WinError(C.get_last_error())
        self.open_event = kernel32.CreateEventW(None, False, False, name + "Open")
        if not self.open_event:
            self.close()
            raise C.WinError(C.get_last_error())

    def request_open(self):
        kernel32.SetEvent(self.open_event)

    def open_requested(self):
        return kernel32.WaitForSingleObject(self.open_event, 0) == 0

    def close(self):
        if getattr(self, "open_event", None):
            kernel32.CloseHandle(self.open_event)
            self.open_event = None
        if self.handle:
            kernel32.CloseHandle(self.handle)
            self.handle = None
