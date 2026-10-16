"""Own-window status that takes neither keyboard focus nor mouse clicks."""

import ctypes as C
import tkinter as tk
from ctypes import wintypes as W

from . import theme, windows


class Indicator:
    def __init__(self, root, width=400):
        self.width = width
        self.window = tk.Toplevel(root)
        self.window.title("Silent Type status")
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.geometry(f"{width}x48+{(root.winfo_screenwidth() - width) // 2}+8")
        self.label = tk.Label(
            self.window,
            text="",
            font=("Segoe UI", 12),
            fg="white",
            bg=theme.STATUS,
            wraplength=width - 32,
            padx=16,
            pady=12,
        )
        self.label.pack(fill="both", expand=True)
        self.window.update_idletasks()
        u = windows.user32
        self.hwnd = u.GetParent(self.window.winfo_id())
        u.GetWindowLongPtrW.argtypes = [W.HWND, C.c_int]
        u.GetWindowLongPtrW.restype = C.c_ssize_t
        u.SetWindowLongPtrW.argtypes = [W.HWND, C.c_int, C.c_ssize_t]
        u.SetWindowLongPtrW.restype = C.c_ssize_t
        u.SetWindowPos.argtypes = [W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT]
        u.SetLayeredWindowAttributes.argtypes = [W.HWND, W.DWORD, W.BYTE, W.DWORD]
        u.SetLayeredWindowAttributes.restype = W.BOOL
        flags = u.GetWindowLongPtrW(self.hwnd, -20)
        u.SetWindowLongPtrW(self.hwnd, -20, flags | 0x08000000 | 0x80 | 0x80000 | 0x20)
        if not u.SetLayeredWindowAttributes(self.hwnd, 0, 255, 2):
            raise C.WinError(C.get_last_error())

    def show(self, text, color=theme.STATUS):
        self.label.configure(text=text, bg=color)
        self.window.update_idletasks()
        u = windows.user32

        class MonitorInfo(C.Structure):
            _fields_ = [("cbSize", W.DWORD), ("rcMonitor", W.RECT), ("rcWork", W.RECT), ("dwFlags", W.DWORD)]

        u.MonitorFromWindow.argtypes = [W.HWND, W.DWORD]
        u.MonitorFromWindow.restype = W.HANDLE
        u.GetMonitorInfoW.argtypes = [W.HANDLE, C.POINTER(MonitorInfo)]
        u.GetMonitorInfoW.restype = W.BOOL
        info = MonitorInfo()
        info.cbSize = C.sizeof(info)
        monitor = u.MonitorFromWindow(u.GetForegroundWindow(), 2)
        if not u.GetMonitorInfoW(monitor, C.byref(info)):
            raise C.WinError(C.get_last_error())
        work = info.rcWork
        width = min(self.width, work.right - work.left - 32)
        self.label.configure(wraplength=width - 32)
        self.window.update_idletasks()
        height = max(48, self.label.winfo_reqheight())
        # NOACTIVATE | SHOWWINDOW. Small strip at the top center of the active display.
        u.SetWindowPos(
            self.hwnd, -1, (work.left + work.right - width) // 2, work.top + 8, width, height, 0x50
        )

    def hide(self):
        windows.user32.SetWindowPos(self.hwnd, -1, 0, 0, 0, 0, 0x93)
