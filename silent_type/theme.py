"""Neutral desktop palette and shared native-widget styles."""

BG = "#f4f5f6"
SURFACE = "#ffffff"
INK = "#172026"
MUTED = "#53616a"
ACCENT = "#087e8b"
ACCENT_DARK = "#06616b"
EDGE = "#c9d0d4"
ERROR = "#8b3535"
SUCCESS = "#14783d"
WORKING = "#805900"


def apply(root):
    from tkinter import font, ttk

    root.configure(background=BG)
    font.nametofont("TkDefaultFont", root).configure(family="Segoe UI", size=10)
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(".", background=BG, foreground=INK, font=("Segoe UI", 10))
    style.configure("TButton", padding=(12, 8), borderwidth=1, focuscolor=ACCENT)
    style.map("TButton", background=[("active", "#e1ecee")], foreground=[("disabled", MUTED)])
    style.configure("Accent.TButton", background=ACCENT_DARK, foreground=SURFACE)
    style.map("Accent.TButton", background=[("active", ACCENT)], foreground=[("disabled", EDGE)])
    style.configure("TCombobox", padding=6, fieldbackground=SURFACE)
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, rowheight=32, borderwidth=1)
    style.map("Treeview", background=[("selected", ACCENT_DARK)], foreground=[("selected", SURFACE)])
    style.configure("Treeview.Heading", padding=(8, 8), font=("Segoe UI", 10, "bold"))
    style.configure("Muted.TLabel", foreground=MUTED)
    style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"))
    style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
