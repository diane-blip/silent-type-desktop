"""Running log of every recognized phrase, appended to a markdown file.

It defaults to `silent-type-log.md` in the machine-local data folder, outside
the source checkout. Set `log_path` in settings.json to use another location.
"""

from datetime import datetime
from pathlib import Path

from .state import DATA

DEFAULT = DATA / "silent-type-log.md"
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
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(HEADER, encoding="utf-8")
    with path.open("rb") as source:
        source.seek(0, 2)
        source.seek(max(0, source.tell() - 4096))
        tail = source.read().decode("utf-8", errors="replace")
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        if day_heading not in tail:
            f.write(f"\n{day_heading}\n\n")
        f.write(f"- **{now:%H:%M}** {text}\n")
