"""The Camera and settings window: camera choice, preview, manual recording, history.

Normal use never needs it; the app runs from the tray. It only builds and updates
widgets and calls back into the app for every action.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

LOG = logging.getLogger(__name__)


class MainWindow:
    def __init__(
        self,
        root,
        *,
        history,
        hold_label,
        camera_names,
        camera,
        on_camera,
        on_preview,
        on_record,
        on_copy,
        on_hide,
    ):
        self.root = root
        self.history = history
        self.on_copy = on_copy
        self.saved_rows = {}
        self.photo = None
        body = ttk.Frame(root, padding=18)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Silent Type", font=("Segoe UI", 22)).pack(anchor="w")
        control_label = (
            f"Click where you want to type, hold {hold_label} and mouth a short phrase. "
            "Release either key to type it. Escape cancels."
            if hold_label
            else "Keyboard control is off in settings. Use Start recording below."
        )
        ttk.Label(body, text=control_label, wraplength=680).pack(anchor="w", pady=(4, 8))
        ttk.Label(
            body,
            text="Start recording saves a phrase here. Stop finishes it; "
            "Cancel recognition stops processing. Camera only.",
            wraplength=680,
        ).pack(anchor="w")
        self.status = tk.StringVar(value="Loading model…")
        ttk.Label(body, textvariable=self.status, wraplength=670).pack(anchor="w", pady=12)

        controls = ttk.Frame(body)
        controls.pack(fill="x")
        ttk.Label(controls, text="Camera").grid(row=0, column=0, sticky="w")
        self.camera = tk.StringVar(value=camera)
        self.camera_select = ttk.Combobox(
            controls, textvariable=self.camera, values=camera_names, state="readonly", width=47
        )
        self.camera_select.grid(row=0, column=1, sticky="ew", padx=8)
        self.camera_select.bind("<<ComboboxSelected>>", lambda _: on_camera(self.camera.get()))
        self.preview_button = ttk.Button(controls, text="Check camera", command=on_preview)
        self.preview_button.grid(row=0, column=2)
        self.record_button = ttk.Button(body, text="Start recording", command=on_record)
        self.record_button.pack(anchor="w", pady=8)
        self.preview_image = ttk.Label(body)
        self.preview_image.pack(pady=8)
        ttk.Label(
            body,
            text="Face forward with your mouth visible. Test short phrases before relying on them.",
            wraplength=670,
        ).pack(anchor="w")

        ttk.Separator(body).pack(fill="x", pady=12)
        ttk.Label(body, text="Recent phrases", font=("Segoe UI", 12)).pack(anchor="w")
        self.rows = ttk.Treeview(body, columns=("phrase", "outcome"), show="headings", height=5)
        self.rows.heading("phrase", text="Recognized text")
        self.rows.heading("outcome", text="Result")
        self.rows.column("phrase", width=430)
        self.rows.column("outcome", width=190)
        self.rows.pack(fill="both", expand=True, pady=6)
        self.rows.bind("<<TreeviewSelect>>", self.select_phrase)
        self.phrase = tk.Text(body, height=3, wrap="word", font=("Segoe UI", 11))
        self.phrase.pack(fill="x")
        self.phrase.configure(state="disabled")

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Copy selected", command=self.copy_selected).pack(side="left")
        ttk.Button(actions, text="Clear history", command=self.clear_history).pack(side="left", padx=8)
        ttk.Button(actions, text="Hide", command=on_hide).pack(side="right")
        ttk.Label(
            body,
            text="Recognition can be wrong. Video is discarded after each phrase.",
            wraplength=670,
        ).pack(anchor="w", pady=(4, 0))
        self.refresh_history()

    def set_camera(self, name):
        self.camera.set(name)

    def set_record_label(self, text):
        self.record_button.configure(text=text)

    def set_previewing(self, previewing):
        self.preview_button.configure(text="Stop camera" if previewing else "Check camera")
        if not previewing:
            self.preview_image.configure(image="")

    def show_preview(self, rgb):
        from PIL import Image, ImageTk

        self.photo = ImageTk.PhotoImage(Image.fromarray(rgb))
        self.preview_image.configure(image=self.photo)

    def refresh_history(self):
        for row in self.rows.get_children():
            self.rows.delete(row)
        self.saved_rows = {str(row[0]): row for row in self.history.recent()}
        for key, row in self.saved_rows.items():
            self.rows.insert("", "end", iid=key, values=(row[2], row[3]))
        if self.saved_rows:
            self.rows.selection_set(next(iter(self.saved_rows)))
        self.select_phrase()

    def select_phrase(self, *_):
        selection = self.rows.selection()
        self.phrase.configure(state="normal")
        self.phrase.delete("1.0", "end")
        if selection:
            self.phrase.insert("1.0", self.saved_rows[selection[0]][2])
        self.phrase.configure(state="disabled")

    def copy_selected(self):
        selection = self.rows.selection()
        if selection:
            self.on_copy(self.saved_rows[selection[0]][2])

    def clear_history(self):
        if messagebox.askyesno("Clear history?", "Delete recognized phrases from this computer?"):
            self.history.clear()
            self.refresh_history()
