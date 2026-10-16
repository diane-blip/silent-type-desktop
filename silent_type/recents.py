"""Recent-phrases popup: left-click the tray icon, click a row (or press its
digit) to copy that phrase to the clipboard.

Compact keyboard-operable recovery list. The neutral palette is independent of
the author's brand; copying is always an explicit action.
"""

import ctypes
import tkinter as tk
import tkinter.font as tkfont

INK = "#172026"
ROW = "#242e35"
HOVER = "#34434d"
EDGE = "#53616a"
PAPER = "#ffffff"
MUTED = "#b8c5cc"
ACCENT = "#8ed8dc"
TRANSPARENT = "#010203"  # never-drawn key color -> real rounded corners


def _round_rect(c: tk.Canvas, x0, y0, x1, y1, r, **kw):
    pts = [
        x0 + r,
        y0,
        x1 - r,
        y0,
        x1,
        y0,
        x1,
        y0 + r,
        x1,
        y1 - r,
        x1,
        y1,
        x1 - r,
        y1,
        x0 + r,
        y1,
        x0,
        y1,
        x0,
        y1 - r,
        x0,
        y0 + r,
        x0,
        y0,
    ]
    return c.create_polygon(pts, smooth=True, **kw)


def _pick_font(root, preferred, fallback="Segoe UI"):
    try:
        families = set(tkfont.families(root))
        for name in preferred:
            if name in families:
                return name
    except Exception:
        pass
    return fallback


def _ellipsize(font: tkfont.Font, text: str, max_px: int) -> str:
    """One display line: collapse whitespace, trim to fit, add an ellipsis."""
    text = " ".join(text.split())
    if font.measure(text) <= max_px:
        return text
    low, high = 0, len(text)
    while low < high:
        mid = (low + high + 1) // 2
        if font.measure(text[:mid] + "…") <= max_px:
            low = mid
        else:
            high = mid - 1
    return text[:low].rstrip() + "…"


class Recents:
    """entries = newest-first list of recognized phrases (max 10). pick(text) is
    called with the chosen full text; open_log() opens the log file. done(cb)
    is called exactly once — with the chosen action, or None on dismissal —
    when the popup closes."""

    def __init__(self, root: tk.Tk, entries, pick, open_log, done):
        self.done = done
        self.finished = False
        self._pressed_row = None

        try:
            s = ctypes.windll.user32.GetDpiForSystem() / 96.0
        except Exception:
            s = 1.0
        text_family = _pick_font(root, ["Segoe UI Variable Text", "Segoe UI"])
        disp_family = _pick_font(root, ["Segoe UI Variable Display", "Segoe UI"])
        row_font = tkfont.Font(family=text_family, size=-int(13 * s))

        pad = int(16 * s)
        row_h = int(38 * s)
        row_gap = int(5 * s)
        head_h = int(26 * s)
        chip = int(24 * s)
        width = int(430 * s)

        # Rows: the entries (or one empty-state row), then "Open the full log".
        digits = [str((i + 1) % 10) for i in range(len(entries))]  # 1..9 then 0
        n_rows = max(len(entries), 1) + 1
        height = pad * 2 + head_h + n_rows * (row_h + row_gap) - row_gap

        self.top = tk.Toplevel(root)
        self.top.overrideredirect(True)
        self.top.attributes("-topmost", True)
        self.top.configure(bg=TRANSPARENT)
        self.top.attributes("-transparentcolor", TRANSPARENT)

        c = tk.Canvas(self.top, width=width, height=height, bg=TRANSPARENT, highlightthickness=0, bd=0)
        c.pack()
        self.canvas = c

        _round_rect(c, 1, 1, width - 1, height - 1, int(20 * s), fill=INK, outline=EDGE, width=max(1, int(s)))

        eyebrow = "Recent phrases"
        c.create_text(
            pad + int(2 * s),
            pad + head_h // 2 - int(3 * s),
            anchor="w",
            text=eyebrow,
            fill=PAPER,
            font=(disp_family, -int(11 * s), "bold"),
        )
        c.create_text(
            width - pad - int(2 * s),
            pad + head_h // 2 - int(3 * s),
            anchor="e",
            text="click to copy · esc",
            fill=MUTED,
            font=(text_family, -int(11 * s)),
        )

        self._row_rects = {}
        label_px = width - pad * 2 - chip - int(38 * s)
        y = pad + head_h

        def add_row(i, chip_char, label, fill_label, cb):
            tag = f"row{i}"
            rect = _round_rect(c, pad, y, width - pad, y + row_h, int(11 * s), fill=ROW, outline="", tags=tag)
            self._row_rects[tag] = rect
            cy = y + row_h // 2
            cx = pad + int(10 * s)
            if chip_char is not None:
                _round_rect(
                    c,
                    cx,
                    cy - chip // 2,
                    cx + chip,
                    cy + chip // 2,
                    chip // 2,
                    fill=ACCENT,
                    outline="",
                    tags=tag,
                )
                c.create_text(
                    cx + chip // 2,
                    cy - int(1 * s),
                    text=chip_char,
                    fill=INK,
                    font=(disp_family, -int(12 * s), "bold"),
                    tags=tag,
                )
            c.create_text(
                cx + chip + int(12 * s),
                cy - int(1 * s),
                anchor="w",
                text=label,
                fill=fill_label,
                font=(text_family, -int(13 * s)),
                tags=tag,
            )
            if cb is not None:
                c.tag_bind(tag, "<Enter>", lambda e, t=tag: self._hover(t, True))
                c.tag_bind(tag, "<Leave>", lambda e, t=tag: self._hover(t, False))
                c.tag_bind(tag, "<ButtonPress-1>", lambda e, t=tag: self._press_row(t))
                c.tag_bind(tag, "<ButtonRelease-1>", lambda e, t=tag, x=cb: self._release_row(t, x))

        if entries:
            for i, text in enumerate(entries):

                def cb(t=text):
                    pick(t)

                add_row(i, digits[i], _ellipsize(row_font, text, label_px), PAPER, cb)
                self.top.bind(digits[i], lambda e, d=digits[i], x=cb: self._digit(e, d, x))
                y += row_h + row_gap
        else:
            add_row(0, None, "Nothing typed yet.", MUTED, None)
            y += row_h + row_gap

        add_row(n_rows - 1, None, "Open the full log · L", ACCENT, open_log)
        self.top.bind("l", lambda event: self._digit(event, "L", open_log))
        self.top.bind("L", lambda event: self._digit(event, "L", open_log))

        self.top.bind("<Escape>", lambda e: self._finish(None))
        self.top.bind("<FocusOut>", lambda e: self._finish(None))

        # Place near the cursor (which just clicked the tray icon), clamped
        # to the screen.
        x = min(max(root.winfo_pointerx() - int(20 * s), 8), root.winfo_screenwidth() - width - 8)
        yy = min(max(root.winfo_pointery() - height + int(10 * s), 8), root.winfo_screenheight() - height - 8)
        self.top.geometry(f"{width}x{height}+{x}+{yy}")
        self.top.focus_force()

    def _hover(self, tag, on):
        self.canvas.itemconfigure(self._row_rects[tag], fill=HOVER if on else ROW)
        self.canvas.configure(cursor="hand2" if on else "")

    def _press_row(self, tag):
        self._pressed_row = tag

    def _release_row(self, tag, cb):
        pressed = self._pressed_row
        self._pressed_row = None
        if pressed == tag:
            self._finish(cb)

    def _digit(self, event, digit, cb):
        # Unicode dictation events are VK_PACKET, not physical digit presses.
        key = ord(digit)
        if event.keycode == key and ctypes.windll.user32.GetAsyncKeyState(key) & 0x8000:
            self._finish(cb)

    def _finish(self, cb):
        if self.finished:
            return
        self.finished = True
        try:
            self.top.destroy()
        except Exception:
            pass
        self.done(cb)
