"""GameBase 64 browser: browse gbc64.sqlite3 with files resolved by data_layout.

Run:  python gamebase64.py      (needs Pillow: pip install pillow)
"""
from ui.app import App

if __name__ == "__main__":
    App().mainloop()
