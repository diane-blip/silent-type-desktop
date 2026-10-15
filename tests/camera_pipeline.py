"""Bounded real camera -> worker -> history test, with no external typing.

Uses the production manual Start/Stop path. Video stays in memory. History is
temporary. Absence of a detectable face is reported separately from control
failure; the operator has not been asked to mouth a test phrase.
"""

import ctypes as C
import json
import logging
import tempfile
from ctypes import wintypes as W
from pathlib import Path
from unittest.mock import patch

from silent_type import windows
from silent_type.app import App
from silent_type.state import History
from silent_type.worker import ManagedRecognizer

decode = ManagedRecognizer.decode


def measured_decode(worker, frames, timestamps, cancelled=lambda: False):
    print(
        json.dumps(
            {
                "captured_frames": len(frames),
                "captured_seconds": timestamps[-1] - timestamps[0] if timestamps else 0,
            }
        ),
        flush=True,
    )
    return decode(worker, frames, timestamps, cancelled)


class CameraPipeline(App):
    def build_window(self):
        super().build_window()
        self.stages = []
        self.test_started = False
        self.finish_scheduled = False
        self.failed = None
        self.root.after(90000, self.timeout)
        self.root.after(100, self.check)

    def post(self, kind, value=None):
        if hasattr(self, "stages"):
            self.stages.append(kind)
        super().post(kind, value)

    def check(self):
        if not self.test_started and self.recognizer is not None:
            assert not hasattr(self, "hotkeys")
            self.test_started = True
            self.start_phrase(None, manual=True)
        if self.phase == "recording" and not self.finish_scheduled:
            u = windows.user32
            u.GetWindowRect.argtypes = [W.HWND, C.POINTER(W.RECT)]
            u.WindowFromPoint.argtypes = [W.POINT]
            u.WindowFromPoint.restype = W.HWND
            u.IsChild.argtypes = [W.HWND, W.HWND]
            rect = W.RECT()
            assert u.GetWindowRect(self.overlay_hwnd, C.byref(rect))
            hit = u.WindowFromPoint(W.POINT((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2))
            assert hit and hit != self.overlay_hwnd and not u.IsChild(self.overlay_hwnd, hit), (
                "Status strip intercepts mouse hit testing"
            )
            self.finish_scheduled = True
            self.root.after(2500, self.finish.set)
        if self.test_started and not self.busy:
            rows = self.history.recent()
            assert "recording" in self.stages, self.status.get()
            assert "working" in self.stages, self.status.get()
            result = {
                "real_camera_recorded": True,
                "real_worker_called": True,
                "recognized_phrase": bool(rows),
                "accuracy": "unverified",
                "external_typing": False,
                "mouse_passes_status_strip": True,
                "device": self.recognizer.device,
            }
            if rows:
                assert rows[0][3] == "saved: recorded in app"
                result["text_length"] = len(rows[0][2])
            else:
                error = self.status.get()
                assert error.startswith(("Face was not visible", "No face found", "No words recognized")), (
                    error
                )
                result["recognition_result"] = error
            print(json.dumps(result), flush=True)
            self.post("quit")
            return
        self.root.after(100, self.check)

    def timeout(self):
        self.failed = "Real camera pipeline timed out: " + self.status.get()
        self.post("quit")


def main():
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s")
    logging.getLogger("silent_type.app").setLevel(logging.INFO)
    with tempfile.TemporaryDirectory() as directory:
        history = History(Path(directory) / "history.sqlite3")
        with (
            patch("silent_type.app.History", return_value=history),
            patch.object(ManagedRecognizer, "decode", measured_decode),
        ):
            app = CameraPipeline()
        assert not app.failed, app.failed
        assert not hasattr(app, "hotkeys")
        assert app.recognizer.closed


if __name__ == "__main__":
    main()
