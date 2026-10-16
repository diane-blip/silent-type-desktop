"""Held Right Ctrl + Right Alt -> real camera -> typing into another process -> camera released.

The production app runs hidden with its real camera stream, hold watcher and
delivery code. Windows key events for the pair are sent with SendInput and always
released in `finally`. Only recognition is replaced with a fixed phrase, so this
proves the keyboard and delivery path, not lip-reading accuracy. The receiving
editor is a disposable window in a separate process; history is temporary.
"""

import ctypes as C
import ctypes.wintypes
import json
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

from silent_type import windows
from silent_type.app import App
from silent_type.state import History, settings
from silent_type.worker import ManagedRecognizer

PHRASE = "delivered by silent type"
EDITOR = r"""
import sys, tkinter as tk
out = sys.argv[1]
root = tk.Tk(); root.title("Silent Type delivery fixture"); root.geometry("520x160+200+200"); root.attributes("-topmost", True)
text = tk.Text(root, font=("Segoe UI", 14)); text.pack(fill="both", expand=True)
def save():
    open(out, "w", encoding="utf-8").write(text.get("1.0", "end-1c")); root.after(200, save)
root.after(100, lambda: (root.lift(), root.focus_force(), text.focus_set())); root.after(200, save)
root.after(60000, root.destroy); root.mainloop()
"""


def key(vk, up):
    flags = (0x1 if vk in (0xA3, 0xA5, 0x5B, 0x5C) else 0) | (0x2 if up else 0)
    event = windows.INPUT(type=1, ki=windows.KEYBOARD(wVk=vk, dwFlags=flags))
    assert windows.user32.SendInput(1, C.byref(event), C.sizeof(event)) == 1


def editor_window(pid):
    found = []

    @C.WINFUNCTYPE(C.c_bool, C.c_void_p, C.c_void_p)
    def visit(hwnd, _):
        owner = C.c_ulong()
        windows.user32.GetWindowThreadProcessId(hwnd, C.byref(owner))
        if owner.value == pid and windows.user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    windows.user32.EnumWindows(visit, 0)
    return found[0] if found else None


def foreground_pid():
    owner = C.c_ulong()
    windows.user32.GetWindowThreadProcessId(windows.user32.GetForegroundWindow(), C.byref(owner))
    return owner.value


def click_center(hwnd):
    """Windows only lets a clicked window take the foreground from another app."""
    rect = C.wintypes.RECT()
    windows.user32.GetWindowRect(hwnd, C.byref(rect))
    windows.user32.SetCursorPos((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2 + 20)
    for flag in (0x2, 0x4):
        event = windows.INPUT(type=0, mi=windows.MOUSE(dwFlags=flag))
        windows.user32.SendInput(1, C.byref(event), C.sizeof(event))


class Delivery(App):
    def post(self, kind, value=None):
        if kind in ("result", "error"):
            self.outcome = (kind, value)
        if kind not in ("preview", "history"):
            self.__dict__.setdefault("stages", []).append(kind if kind != "status" else f"status: {value}")
        super().post(kind, value)


def main():
    work = Path(tempfile.mkdtemp(prefix="silent-type-delivery-"))
    received = work / "editor.txt"
    script = work / "editor.py"
    script.write_text(EDITOR, encoding="utf-8")
    editor = subprocess.Popen([getattr(sys, "_base_executable", sys.executable), str(script), str(received)])
    report = {"recognition": "fixed phrase (not lip accuracy)"}
    holder = {}

    def drive():
        app = None
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                app = holder.get("app")
                ready = app and getattr(app, "recognizer", None) and getattr(app, "feed", None)
                if ready and received.exists():
                    break
                time.sleep(0.1)
            else:
                report["failure"] = "app/editor not ready"
                return
            hwnd = editor_window(editor.pid)
            if hwnd:
                click_center(hwnd)
            time.sleep(1)
            report["destination_is_editor"] = foreground_pid() == editor.pid
            if not report["destination_is_editor"]:
                report["failure"] = "editor never reached the foreground; no keys pressed"
                return
            pressed = time.monotonic()
            try:
                key(config["hold_pair"][0], False)
                time.sleep(0.05)
                key(config["hold_pair"][1], False)
                # The camera opens on the hold, so the first phrase waits for it.
                while app.phase != "recording" and time.monotonic() - pressed < 6:
                    time.sleep(0.01)
                report["press_to_recording_seconds"] = round(time.monotonic() - pressed, 2)
                time.sleep(2)
            finally:
                key(config["hold_pair"][1], True)
                key(config["hold_pair"][0], True)
            end = time.monotonic() + 15
            while time.monotonic() < end and not getattr(app, "outcome", None):
                time.sleep(0.1)
            time.sleep(app.config["camera_warm_seconds"] + 2)
            report["camera_released_after_phrase"] = not app.feed.running()
            app.feed.ensure()
            app.feed.live.wait(8)
            app.post("toggle")  # the tray's Silent Type on switch
            time.sleep(1.5)
            report["camera_released_when_switched_off"] = (
                app.feed.live.is_set() is False and not app.feed.running()
            )
        finally:
            report["outcome"] = getattr(app, "outcome", None)
            report["stages"] = getattr(app, "stages", [])
            report["editor_text"] = received.read_text(encoding="utf-8") if received.exists() else None
            if app:
                app.post("quit")

    config = settings()
    report["held_pair"] = config["hold_pair"]
    config.update(
        hold_enabled=True, punctuate=False, camera_warm_seconds=3, log_path=str(work / "phrases.md")
    )
    history = History(work / "history.sqlite3")
    threading.Thread(target=drive, daemon=True).start()
    original_init = Delivery.__init__

    def capture_init(self, *args, **kwargs):
        holder["app"] = self
        original_init(self, *args, **kwargs)

    with (
        patch.object(ManagedRecognizer, "decode", lambda self, frames, times, cancelled=None: (PHRASE, 0.1)),
        patch.object(Delivery, "__init__", capture_init),
    ):
        Delivery(config=config, history=history)
    editor.terminate()
    time.sleep(0.5)
    report["modifiers_released"] = not windows.modifiers_down()
    report["held_after"] = [
        hex(k) for k in (0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5, 0x5B, 0x5C) if windows.down(k)
    ]
    report["passed"] = (
        report.get("editor_text") == PHRASE[0].upper() + PHRASE[1:] + " "
        and report["modifiers_released"]
        and report.get("press_to_recording_seconds", 9) < 6
        and report.get("camera_released_after_phrase") is True
        and report.get("camera_released_when_switched_off") is True
    )
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
