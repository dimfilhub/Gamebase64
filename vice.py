"""Finding VICE, preparing C64 images and launching games."""
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

from config import Config
from data_layout import DataLayout

# VICE joystick devices (-joydev2): 1 = numpad, 2 = keyset 1, 3 = keyset 2, 4+ = real joysticks.
CONTROLLERS = {"numpad": ("Keyboard (numpad)", "1"),
               "keyset": ("Keyboard (VICE keyset 1)", "2"),
               "joystick": ("Real joystick / gamepad", "4")}
DEFAULT_CONTROLLER = "keyset"


def load_controller_settings(config: Config):
    """(controller, extra_args) from config.json, with defaults filled in."""
    controller = config.get("controller", DEFAULT_CONTROLLER)
    if controller not in CONTROLLERS:
        controller = DEFAULT_CONTROLLER
    return controller, str(config.get("vice_args", "") or "")


class LaunchError(Exception):
    """Raised when a game cannot be launched; the message is user-facing."""


class ViceLocator:
    NAMES = ("x64sc", "x64")

    def __init__(self, layout: DataLayout, config: Config):
        self.layout = layout
        self.config = config

    @staticmethod
    def normalize(p):
        """Accept a VICE folder/.app and return the real x64sc executable inside it."""
        p = Path(p)
        if p.is_dir():
            # x64sc.app in the VICE 3.x dmg is only a launcher droplet; the real binary
            # lives in the sibling bin/ (or VICE.app/Contents/Resources/bin).
            bases = [p] + ([p.parent] if p.suffix == ".app" else [])
            for base in bases:
                for sub in ("", "Contents/Resources/bin", "bin", "VICE.app/Contents/Resources/bin",
                            "x64sc.app/Contents/MacOS"):
                    for name in ("x64sc", "x64sc.exe"):
                        if (base / sub / name).is_file():
                            return base / sub / name
        return p

    def find(self):
        """Locate x64sc: env var, saved config, data/vice, PATH, usual places."""
        candidates = [os.environ.get("VICE_PATH"), self.config.get("vice"),
                      self.layout.vice_dir / "x64sc.exe", self.layout.vice_dir / "x64sc"]
        candidates += [shutil.which(n) for n in self.NAMES]
        candidates += ["/Applications/vice-arm64-gtk3/x64sc.app/Contents/MacOS/x64sc",
                       "/Applications/vice-x86_64-gtk3/x64sc.app/Contents/MacOS/x64sc",
                       "/Applications/VICE/x64sc.app/Contents/MacOS/x64sc",
                       "/Applications/x64sc.app/Contents/MacOS/x64sc",
                       "/opt/homebrew/bin/x64sc", "/usr/local/bin/x64sc",
                       r"C:\Program Files\VICE\bin\x64sc.exe",
                       r"C:\Program Files\GTK3VICE\bin\x64sc.exe"]
        for c in candidates:
            if c and self.normalize(c).is_file():
                return self.normalize(c)
        return None

    def remember(self, path):
        """Validate and persist a user-chosen executable; returns it or None."""
        exe = self.normalize(path)
        if not exe.is_file():
            return None
        self.config.set("vice", str(exe))
        return exe


class ImagePreparer:
    # Images VICE can autostart, in order of preference when no FileToRun is given.
    IMAGE_EXTS = (".d64", ".g64", ".d71", ".d81", ".t64", ".tap", ".crt", ".prg", ".p00",
                  ".x64", ".d80", ".d82", ".lnx", ".vsf")

    def __init__(self, layout: DataLayout):
        self.layout = layout

    def prepare(self, ga_id, zip_path, file_to_run):
        """Extract the game's image from its zip into data/cache/run/{id}.
        Returns the path to autostart. Extracting by basename only avoids any
        path-traversal from zip entries; the whole zip is extracted so multi-file
        images and extra disk sides sit next to each other."""
        run_dir = self.layout.cache / "run" / str(ga_id)
        shutil.rmtree(run_dir, ignore_errors=True)
        run_dir.mkdir(parents=True)
        with zipfile.ZipFile(zip_path) as z:
            members = [i for i in z.infolist() if not i.is_dir()]
            images = sorted((i for i in members if Path(i.filename).suffix.lower() in self.IMAGE_EXTS),
                            key=lambda i: (self.IMAGE_EXTS.index(Path(i.filename).suffix.lower()),
                                           i.filename.lower()))
            wanted = None
            if file_to_run:
                wanted = next((i for i in images
                               if Path(i.filename).name.lower() == Path(file_to_run).name.lower()), None)
            first = wanted or (images[0] if images else None)
            if not first:
                raise ValueError("No C64 image (.d64/.t64/.tap/.crt/.prg/...) found in the zip.")
            first_path = None
            for info in members:
                target = run_dir / Path(info.filename).name
                with z.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                if info is first:
                    first_path = target
        return first_path


class ViceLauncher:
    def __init__(self, layout: DataLayout, preparer: ImagePreparer, config: Config):
        self.layout = layout
        self.preparer = preparer
        self.config = config  # controller and extra arguments are read on every launch

    def launch(self, vice, game, zip_path, file_to_run):
        try:
            image = self.preparer.prepare(game.id, zip_path, file_to_run)
        except (zipfile.BadZipFile, ValueError, OSError) as e:
            raise LaunchError(f"{game.name}\n\n{e}") from e
        controller, extra = load_controller_settings(self.config)
        cmd = [str(vice), "-fullscreen", "-joydev2", CONTROLLERS[controller][1]]
        rc = self.layout.vice_dir / "vicerc"
        if rc.is_file():
            cmd += ["-config", str(rc)]
        if extra.strip():
            cmd += extra.split()
        cmd += ["-autostart", str(image)]
        try:
            subprocess.Popen(cmd, cwd=image.parent)
        except OSError as e:
            raise LaunchError(str(e)) from e
