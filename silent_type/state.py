"""Machine-local settings and recognized-text recovery."""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Silent Type"
MODEL_NAME = "vsr_trlrs2lrs3vox2avsp_base.pth"
FACE_MODEL_NAME = "blaze_face_short_range.tflite"


def data_dir():
    DATA.mkdir(parents=True, exist_ok=True)
    return DATA


def settings():
    defaults = {
        "camera": "",
        "device": "auto",
        "beam": 4,
        "max_seconds": 600,
        "hold_enabled": True,
        "hold_pair": [0xA3, 0xA5],
        "camera_warm_seconds": 15,
        # Exact casing restored for names the model recognizes as words.
        "names": [],
        "log_path": "",
        "env_file": "",
        "model_path": str(DATA / "models" / MODEL_NAME),
        "face_model_path": str(DATA / "models" / FACE_MODEL_NAME),
    }
    path = DATA / "settings.json"
    if path.exists():
        defaults.update(json.loads(path.read_text(encoding="utf-8")))
    return defaults


def save_settings(config):
    path = data_dir() / "settings.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


class History:
    def __init__(self, path=None):
        self.path = path or data_dir() / "history.sqlite3"
        with self.connect() as con:
            con.execute(
                "CREATE TABLE IF NOT EXISTS phrases (id INTEGER PRIMARY KEY, created TEXT, text TEXT, outcome TEXT)"
            )

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.path, timeout=5)
        try:
            with con:
                yield con
        finally:
            con.close()

    def add(self, text):
        with self.connect() as con:
            cur = con.execute(
                "INSERT INTO phrases(created,text,outcome) VALUES(?,?,?)",
                (datetime.now(UTC).isoformat(), text, "saved"),
            )
            return cur.lastrowid

    def mark(self, item, outcome):
        with self.connect() as con:
            con.execute("UPDATE phrases SET outcome=? WHERE id=?", (outcome, item))

    def recent(self):
        with self.connect() as con:
            return con.execute(
                "SELECT id,created,text,outcome FROM phrases ORDER BY id DESC LIMIT 100"
            ).fetchall()

    def clear(self):
        with self.connect() as con:
            con.execute("DELETE FROM phrases")


def format_text(text, names):
    """Restore case only; never guess at names or rewrite the recognized words."""
    import re

    text = " ".join(text.split()).strip()
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\bi\b", "I", text)
    for name in sorted(names, key=len, reverse=True):
        text = re.sub(
            r"(?<!\w)" + re.escape(name) + r"(?!\w)", lambda _match, name=name: name, text, flags=re.I
        )
    return text[0].upper() + text[1:]
