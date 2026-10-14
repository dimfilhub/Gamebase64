"""Build a standalone executable for the current OS with PyInstaller (run: python build.py).

Needs: pip install pyinstaller pillow
The database and the data/vice folder are copied next to the app; the (large) game data
folder is chosen by the user in Settings, or placed next to the app as data/.
"""
import shutil
import sys
from pathlib import Path

import PyInstaller.__main__

NAME = "Gamebase64"
separator = ";" if sys.platform == "win32" else ":"
args = [
    "gamebase64.py",
    "--name", NAME,
    "--windowed",
    "--noconfirm",
    "--add-data", f"README.md{separator}.",
    "--add-data", f"images{separator}images",
]
if sys.platform != "darwin":  # Windows/Linux: single executable in dist/, next to the database
    args.append("--onefile")
PyInstaller.__main__.run(args)

# Ship the database and VICE config next to the app, where DataLayout looks for them.
dist = Path("dist")
shutil.copy("gbc64.sqlite3", dist / "gbc64.sqlite3")
shutil.copytree("data/vice", dist / "data" / "vice", dirs_exist_ok=True)
