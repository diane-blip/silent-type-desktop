"""Bounded physical hold/camera/model review; never inserts or saves settings."""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import theme
from .app import App
from .state import History, settings


class Acceptance(App):
    def __init__(self, seconds, receipt, history):
        self.seconds = seconds
        self.receipt = receipt
        self.started = time.monotonic()
        self.ready_at = None
        self.stages = []
        self.ending = False
        config = settings()
        config.update(hold_enabled=True)
        config["log_path"] = str(history.path.parent / "phrases.md")
        super().__init__(config=config, history=history, review_only=True)
        if hasattr(self, "stop"):
            self.write_receipt(False)

    def build_indicator(self):
        from .indicator import Indicator

        self.strip = Indicator(self.root, width=680)
        self.indicator, self.indicator_label, self.overlay_hwnd = (
            self.strip.window,
            self.strip.label,
            self.strip.hwnd,
        )
        self.show_indicator("SILENT TYPE REVIEW TEST · loading model…", theme.STATUS)
        self.root.after(250, self.check)

    def post(self, kind, value=None):
        # Stage names only; recognized words stay in the temporary test history.
        if kind in (
            "ready",
            "hold_start",
            "hold_finish",
            "hold_cancel",
            "recording",
            "working",
            "result",
            "error",
            "idle",
        ):
            self.stages.append({"stage": kind, "seconds": round(time.monotonic() - self.started, 2)})
        super().post(kind, value)

    def write_receipt(self, running=True):
        self.receipt.parent.mkdir(parents=True, exist_ok=True)
        value = {
            "running": running,
            "review_only": True,
            "pair": self.hold_control.label() if self.hold_control else None,
            "model_ready": self.recognizer is not None,
            "phase": self.phase,
            "status": self.status.get(),
            "stages": self.stages[-100:],
            "external_typing": False,
            "persistent_settings_changed": False,
            "recognized_phrases": len(self.history.recent()),
        }
        temporary = self.receipt.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temporary.replace(self.receipt)

    def check(self):
        if self.stop.is_set():
            return
        now = time.monotonic()
        if self.recognizer is not None and self.ready_at is None:
            self.ready_at = now
            if not self.busy:
                self.show_indicator(
                    f"REVIEW TEST READY · hold {self.hold_control.label()}\nWait for Recording, mouth a short sentence, release. Nothing typed into apps.",
                    theme.STATUS,
                )
        self.write_receipt()
        if not self.ending and (
            (self.ready_at is not None and now - self.ready_at >= self.seconds)
            or now - self.started >= self.seconds + 70
        ):
            self.ending = True
            self.hold_control = None
            self.cancel.set()
            self.show_indicator("Review test ended · keyboard control is off", theme.STATUS)
            self.root.after(5000, lambda: self.post("quit"))
        self.root.after(250, self.check)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--receipt", type=Path, default=Path("build/physical-acceptance.json"))
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not 30 <= args.seconds <= 300:
        parser.error("seconds must be between 30 and 300")
    if args.child:
        with tempfile.TemporaryDirectory(prefix="silent-type-review-") as directory:
            Acceptance(args.seconds, args.receipt, History(Path(directory) / "history.sqlite3"))
        return
    # Independent deadline survives a blocked UI/camera. Kill only this owned tree,
    # including Windows venv redirector children and its recognition worker.
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with (args.receipt.parent / "physical-acceptance.log").open("w", encoding="utf-8") as log:
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "silent_type.acceptance",
                "--child",
                "--seconds",
                str(args.seconds),
                "--receipt",
                str(args.receipt),
            ],
            stdout=log,
            stderr=log,
        )
        try:
            child.wait(timeout=args.seconds + 85)
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["taskkill", "/PID", str(child.pid), "/T", "/F"],
                stdout=log,
                stderr=log,
                timeout=15,
                check=False,
            )
            child.wait(timeout=15)


if __name__ == "__main__":
    main()
