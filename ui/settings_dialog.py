import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from data_layout import DataLayout
from ui.style import BACKGROUND_COLOR
from vice import CONTROLLERS, load_controller_settings


class SettingsDialog(tk.Toplevel):
    """Controller, VICE executable and arguments, and the data folder."""

    def __init__(self, parent, layout, config, on_data_changed=None, on_populate=None, locator=None):
        super().__init__(parent)
        self.title("Settings")
        self.configure(background=BACKGROUND_COLOR)
        self.transient(parent)
        self.resizable(False, False)
        self.layout, self.config, self.on_data_changed = layout, config, on_data_changed
        self.locator = locator
        self.on_populate = on_populate  # opens the Populate folders window
        controller, extra = load_controller_settings(config)

        box = ttk.LabelFrame(self, text="Controller (joystick port 2)", padding=10)
        box.pack(fill="x", padx=10, pady=10)
        self.controller = tk.StringVar(self, value=controller)
        for key, (label, _joydev) in CONTROLLERS.items():
            ttk.Radiobutton(box, text=label, variable=self.controller,
                            value=key).pack(anchor="w")

        vf = ttk.LabelFrame(self, text="VICE x64sc executable (or folder / x64sc.app)", padding=10)
        vf.pack(fill="x", padx=10, pady=(0, 10))
        found = locator.find() if locator else None
        self.vice_var = tk.StringVar(self, value=str(found) if found else "")
        ttk.Entry(vf, textvariable=self.vice_var, width=50).grid(row=0, column=0, sticky="ew")
        ttk.Button(vf, text="Browse...", command=self._browse_vice).grid(row=0, column=1, padx=(5, 0))
        ttk.Label(vf, text="Extra arguments:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.args_var = tk.StringVar(self, value=extra)
        ttk.Entry(vf, textvariable=self.args_var, width=50).grid(row=2, column=0, columnspan=2, sticky="ew")
        vf.columnconfigure(0, weight=1)

        df = ttk.LabelFrame(self, text="Data folder (already populated)", padding=10)
        df.pack(fill="x", padx=10, pady=(0, 10))
        self.data_var = tk.StringVar(self, value=str(layout.data))
        ttk.Entry(df, textvariable=self.data_var, width=50).grid(row=0, column=0, sticky="ew")
        ttk.Button(df, text="Browse...", command=self._browse_data).grid(row=0, column=1, padx=(5, 0))
        ttk.Button(df, text="Default", command=lambda: self.data_var.set(
            str(layout.root / "data"))).grid(row=0, column=2, padx=(5, 0))
        df.columnconfigure(0, weight=1)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(bar, text="Cancel", command=self.destroy).pack(side="right")
        ttk.Button(bar, text="Save", command=self._save).pack(side="right", padx=(0, 5))
        self.bind("<Escape>", lambda _e: self.destroy())
        self.grab_set()

    def _browse_data(self):
        d = filedialog.askdirectory(parent=self, title="Select the populated data folder",
                                    initialdir=self.data_var.get(), mustexist=True)
        if d:
            self.data_var.set(d)

    def _browse_vice(self):
        p = filedialog.askopenfilename(parent=self, title="Select the VICE x64sc executable")
        if not p and sys.platform == "darwin":
            # macOS .app bundles are directories
            p = filedialog.askdirectory(parent=self, title="Select the VICE folder or x64sc.app")
        if p:
            self.vice_var.set(p)

    @staticmethod
    def _folder_problem(data):
        """Describe what is wrong with a data folder, or None if it is complete and populated."""
        probe = DataLayout(data=data)
        if not all(d.is_dir() for d in probe.all_dirs):
            return "does not have the correct folder structure"
        if not any(p.is_file() for p in probe.games.rglob("*")):
            return "has no game files (it is not populated)"
        return None

    def _save(self):
        data = Path(self.data_var.get().strip() or self.layout.root / "data").expanduser()
        changed = data != self.layout.data
        populate = False
        problem = self._folder_problem(data) if changed else None
        if problem:
            answer = messagebox.askyesnocancel(
                "Data folder needs setting up",
                f"The selected data folder {problem}:\n{data}\n\n"
                "Yes: use it and open the Populate folders window to create/populate it\n"
                "No: use it as it is\nCancel: go back",
                parent=self)
            if answer is None:
                return
            populate = answer
        vice = self.vice_var.get().strip()
        if vice and self.locator and not self.locator.remember(vice):
            messagebox.showerror("VICE", f"Not an executable file:\n{vice}", parent=self)
            return
        try:
            self.config.set("controller", self.controller.get())
            self.config.set("vice_args", self.args_var.get().strip())
            if changed:
                self.layout.set_data(data)
        except OSError as e:
            messagebox.showerror("Could not save settings", str(e), parent=self)
            return
        self.destroy()
        if changed and self.on_data_changed:
            self.on_data_changed()
        if populate and self.on_populate:
            self.on_populate()
