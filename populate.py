"""Extract the zips in sources/ into the data/ tree.

Usage: python3 populate.py [--dry-run]

Every GB64 zip holds one top-level folder named like the zip (Games.zip -> Games/...),
and that folder name is the first part of the paths stored in the database.
"""
import sys
import zipfile
from pathlib import Path, PurePosixPath

from data_layout import DataLayout

# Zips whose folder holds runnable images (Extras.Type = 1)
RUNNABLE = ("Disks", "Tapes", "Carts", "Coverdisks", "Covertapes", "PD-Disks", "SceneMags")
# Zips of plain extras (manuals, covers, adverts, videos…)
EXTRAS = ("Cover", "Adverts", "Docs", "Books", "Magcover", "Missing", "Maps", "Longplays",
          "Tips", "Listings", "Videos", "mp3s", "mkv", "Trailer", "Photos", "Type-Ins")


class Populator:
    """Existing files with the same size are skipped, so it can be re-run safely."""

    def __init__(self, layout: DataLayout, log=print):
        self.layout = layout
        self.log = log  # callable(str) receiving progress lines

    @property
    def plan(self):
        """zip name -> (zip-internal prefix to strip, destination folder).
        Entries outside the prefix are ignored. Zip names are matched case-insensitively."""
        l = self.layout
        plan = {
            "Games.zip":       ("Games/",       l.games),
            "Screenshots.zip": ("Screenshots/", l.screenshots),
            "Music.zip":       ("",             l.music_dir),  # optional HVSC: GAMES/, MUSICIANS/, DEMOS/
        }
        for name in RUNNABLE:
            plan[f"{name}.zip"] = (f"{name}/", l.extras_runnable / name)
        for name in EXTRAS:
            plan[f"{name}.zip"] = (f"{name}/", l.extras_dir / name)
        return plan

    def check_sources(self, folder=None):
        """Compare `folder` (default: the sources folder) with the zips the plan expects.
        Returns (found, missing, broken, extra) lists of zip names."""
        folder = Path(folder or self.layout.sources)
        present = {p.name.casefold(): p.name for p in folder.iterdir()
                   if p.is_file()} if folder.is_dir() else {}
        expected = list(self.plan)
        found = [present[n.casefold()] for n in expected if n.casefold() in present]
        broken = [n for n in found if not zipfile.is_zipfile(folder / n)]
        found = [n for n in found if n not in broken]
        missing = [n for n in expected if n.casefold() not in present]
        wanted = {n.casefold() for n in expected}
        extra = sorted(n for k, n in present.items() if k not in wanted and k.endswith(".zip"))
        return found, missing, broken, extra

    def extract(self, zip_path, prefix, dest, dry=False):
        n = skipped = 0
        dest_root = dest.resolve()
        parents = {}  # parent folder -> its real on-disk path (case/Unicode-insensitive match)
        with zipfile.ZipFile(zip_path) as z:
            for info in z.infolist():
                name = info.filename
                if info.is_dir() or name.startswith("__MACOSX") or name.endswith(".DS_Store"):
                    continue
                if not name.startswith(prefix):
                    continue
                rel = PurePosixPath(name[len(prefix):])
                if not rel.parts:
                    continue
                target = (dest / Path(*rel.parts)).resolve()
                if dest_root != target and dest_root not in target.parents:  # zip-slip guard
                    self.log(f"  skip unsafe path: {name}")
                    continue
                if target.parent not in parents:
                    parents[target.parent] = self.layout.resolve(target.parent)
                target = parents[target.parent] / target.name
                if target.exists() and target.stat().st_size == info.file_size:
                    skipped += 1
                    continue
                n += 1
                if not dry:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with z.open(info) as src, open(target, "wb") as out:
                        while chunk := src.read(1 << 20):
                            out.write(chunk)
        return n, skipped

    def run(self, dry=False):
        found, missing, broken, _extra = self.check_sources()
        plan = {k.casefold(): v for k, v in self.plan.items()}
        for name in missing:
            self.log(f"missing: {name}")
        for name in broken:
            self.log(f"unreadable: {name}")
        for name in found:
            prefix, dest = plan[name.casefold()]
            n, s = self.extract(self.layout.sources / name, prefix, dest, dry)
            self.log(f"{name}: {'would extract' if dry else 'extracted'} {n}, skipped {s}")


if __name__ == "__main__":
    Populator(DataLayout()).run(dry="--dry-run" in sys.argv)
