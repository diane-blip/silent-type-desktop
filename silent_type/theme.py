"""Neutral desktop palette and shared native-widget styles."""

BG = "#F5F5F5"
SURFACE = "#FFFFFF"
INK = "#171717"
MUTED = "#626262"
ACCENT = "#AD8326"
ACCENT_DARK = "#8A6820"
ACCENT_LIGHT = "#E8DBBE"
EDGE = "#C8C8C8"
SELECTED = "#E2E2E2"
STATUS = "#252525"
ERROR = SUCCESS = WORKING = STATUS  # Status words carry meaning on a neutral strip.
RECENTS_ROW = "#252525"
RECENTS_HOVER = "#333333"
RECENTS_EDGE = "#4B4B4B"
RECENTS_MUTED = "#B8B8B8"


def apply(root):
    from tkinter import font, ttk

    root.configure(background=BG)
    font.nametofont("TkDefaultFont", root).configure(family="Segoe UI", size=10)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=INK, font=("Segoe UI", 10))
    style.configure(
        "TButton",
        padding=(12, 8),
        borderwidth=1,
        focuscolor=ACCENT,
        background=BG,
        bordercolor="#9A9A9A",
        lightcolor=BG,
        darkcolor=BG,
    )
    style.map("TButton", background=[("active", "#E6E6E6")], foreground=[("disabled", MUTED)])
    # White on gold is the approved brand pairing, not an AA small-text contrast claim.
    style.configure("Accent.TButton", background=ACCENT, foreground=SURFACE)
    style.map(
        "Accent.TButton",
        background=[("disabled", SELECTED), ("active", ACCENT_DARK)],
        foreground=[("disabled", MUTED)],
    )
    style.configure("TCombobox", padding=6, fieldbackground=SURFACE)
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE)],
        selectbackground=[("readonly", SELECTED)],
        selectforeground=[("readonly", INK)],
    )
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, rowheight=32, borderwidth=1)
    style.map("Treeview", background=[("selected", SELECTED)], foreground=[("selected", INK)])
    style.configure("Treeview.Heading", padding=(8, 8), font=("Segoe UI", 10, "bold"))
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
    style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
