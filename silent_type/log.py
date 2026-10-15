"""Running log of every recognized phrase, appended to a markdown file.

Same format as Dictate's log. It defaults to `silent-type-log.md` in this folder
(ignored by Git, since it holds everything you say). Set `log_path` in
settings.json to put it somewhere else, such as a synced notes folder.
"""

from datetime import datetime
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "silent-type-log.md"
HEADER = """# Silent Type log

Everything Silent Type recognized, newest at the bottom. Appended before each insertion.
"""


def log_path(config):
    configured = config.get("log_path")
    return Path(configured).expanduser() if configured else DEFAULT


def append_log(text, path=DEFAULT):
    text = " ".join(text.split())
    if not text:
        return
    now = datetime.now()
    day_heading = f"## {now:%Y-%m-%d}"
    if not path.exists():
        path.write_text(HEADER, encoding="utf-8")
    tail = path.read_text(encoding="utf-8")[-4000:]
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        if day_heading not in tail:
            f.write(f"\n{day_heading}\n\n")
        f.write(f"- **{now:%H:%M}** {text}\n")
