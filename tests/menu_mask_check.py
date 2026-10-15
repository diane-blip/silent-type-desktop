"""Does releasing Right Alt after Right Ctrl open a window's menu, with and without the mask key?

Opens a disposable topmost window with a menu bar in a separate process, clicks
it to make it the foreground window, holds the pair through Windows key events
(always released), and reads the window's menu mode. Hands off the keyboard for
about three seconds.
"""

import ctypes as C
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from silent_type import windows
from tests.delivery_pipeline import click_center, editor_window, foreground_pid, key

WINDOW = r"""
import tkinter as tk
root = tk.Tk(); root.title("Silent Type menu check"); root.geometry("420x160+240+240")
root.attributes("-topmost", True)
bar = tk.Menu(root); file = tk.Menu(bar, tearoff=0); file.add_command(label="Close", command=root.destroy)
bar.add_cascade(label="File", menu=file); root.config(menu=bar)
root.after(30000, root.destroy); root.mainloop()
"""


def hold_and_release(mask):
    try:
        key(0xA3, False)
        time.sleep(0.05)
        key(0xA5, False)
        time.sleep(0.3)
        if mask:
            windows.mask_menu_key()
        time.sleep(0.1)
    finally:
        key(0xA5, True)
        key(0xA3, True)
    time.sleep(0.3)
    hwnd = windows.user32.GetForegroundWindow()
    in_menu = windows.in_menu_mode(hwnd)
    if in_menu:
        windows.user32.PostMessageW(hwnd, 0x001F, 0, 0)  # WM_CANCELMODE leaves the menu
        time.sleep(0.2)
    return in_menu


def main():
    script = Path(tempfile.mkdtemp(prefix="silent-type-menu-")) / "window.py"
    script.write_text(WINDOW, encoding="utf-8")
    window = subprocess.Popen([getattr(sys, "_base_executable", sys.executable), str(script)])
    report = {}
    try:
        for _ in range(50):
            hwnd = editor_window(window.pid)
            if hwnd:
                break
            time.sleep(0.1)
        time.sleep(0.5)
        results = {}
        for label, mask in (("without_mask", False), ("with_mask", True)):
            click_center(editor_window(window.pid))
            time.sleep(0.4)
            if foreground_pid() != window.pid:
                report["failure"] = "test window never reached the foreground; no keys pressed"
                break
            results[label] = hold_and_release(mask)
        report.update(menu_opened=results)
        report["modifiers_released"] = not windows.modifiers_down()
        report["passed"] = results.get("with_mask") is False and report["modifiers_released"]
    finally:
        window.terminate()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("passed") else 1)


if __name__ == "__main__":
    C.windll.user32.SetProcessDPIAware()
    main()
