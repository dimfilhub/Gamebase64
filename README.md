# Gamebase64 Browser and Player

Gamebase64 Browser and Player is a desktop browser and player for the **GameBase 64 (GB64)** collection of Commodore 64 games. It reads the bundled game database (`gbc64.sqlite3`, converted from the original `GBC_v19.mdb` for easier access), shows each game's metadata, screenshot, cover, music and extras (manuals, adverts, maps, tips, magazine covers…), and launches games in the [VICE](https://vice-emu.sourceforge.io/) emulator with one click.

The app does not ship the game files. You supply the GB64 source zips, and the app extracts them into a `data/` folder.

## What the app does

- **Browse and filter** the game list by genre, year, publisher and developer, using the dropdown filters.
- **Game details**: the *Info* tab (publisher, developer, programmer, artist, musician, genre, language, players, cracker, link…), the *Notes* tab (comments and memo) and the *Extras* tab (adverts, covers, manuals, maps, tips and so on, with missing files marked).
- **Preview**: switch between the in-game screenshot and the cover.
- **Action buttons**: *Screenshot*, *Cover*, *Reveal game file* (show the zip in Finder/Explorer), and *Launch in VICE*.
- **Launch in VICE**: extracts the game's zip into `data/cache/run/<id>` and starts `x64sc -autostart` on the image named in the database (`FileToRun`), or else the first `.d64/.g64/.t64/.tap/.crt/.prg…` found. It runs fullscreen with the chosen controller on joystick port 2.

## Using the app

- **Search**: type in the *Search* field above the list to filter games by name as you type. Click **Clear** to empty the field and show all games again.
- **Filters**: the dropdowns below the search box narrow the list by genre, year, publisher and developer. They combine with the search text.
- **Selecting a game**: click a game in the list to see its screenshot, details and extras. Buttons are greyed out when the matching file is missing.
- **Launching a game**: select it and click **Launch in VICE**, or double-click it in the list. VICE must be installed (see *Settings*), and the game's zip must be present in the data folder.
- **Other buttons**: **Populate folders…** extracts the source zips, **Settings…** configures the controller, VICE and data folder, and **Quit** closes the app.

## Requirements

- Python 3 with Tk (the standard `tkinter`)
- [Pillow](https://python-pillow.org/) (`pip install -r requirements.txt`)
- [VICE](https://vice-emu.sourceforge.io/) (the `x64sc` emulator) to launch games. Browsing works without it.

Run the app:

```sh
python gamebase64.py
```

## Populating the folders

The app finds files under a **data folder** (default `./data` next to the app). Its layout follows the paths stored in the database:

```
data/
├── games/              game zips, in the collection's sub-folders (0, a1, a2, b1 … e …)
├── screenshots/        in-game screenshots (same sub-folders)
├── music/              SID files: GAMES, MUSICIANS, DEMOS (HVSC layout)
├── extras/             Cover, Adverts, Docs, Books, Magcover, Maps, Tips, Videos, mp3s…
├── extras_runnable/    extras that can run in the emulator (Disks, Tapes, Carts, Coverdisks, Covertapes, PD-Disks, SceneMags)
├── covers/             generated front covers ({GA_Id}.jpg)
├── cache/              temporary images created at launch
└── vice/               optional vicerc config (and x64sc.exe on Windows)
```

### 1. Get the source zips

The app does not include the game files, so you must download them first. At minimum you need the games; screenshots, music and extras are optional but fill in the previews and extras. The GameBase 64 collection comes from the GB64 project: <http://www.gb64.com/>. All credit for the GB64 data and files goes to that project and its contributors.

Put the zips in the **sources folder** (default `./sources`). Each zip holds one top-level folder named like the zip, which is the first part of the paths in the database, so the zips are recognised by name (case-insensitive):

| Zip | Extracted to |
| --- | --- |
| `Games.zip` | `data/games` (sub-folders `0`, `a1` … `e`) |
| `Screenshots.zip` | `data/screenshots` |
| `Disks.zip`, `Tapes.zip`, `Carts.zip`, `Coverdisks.zip`, `Covertapes.zip`, `PD-Disks.zip`, `SceneMags.zip` | `data/extras_runnable/<name>` |
| `Cover.zip`, `Adverts.zip`, `Docs.zip`, `Books.zip`, `Magcover.zip`, `Missing.zip`, `Maps.zip`, `Tips.zip`, `Listings.zip`, `Longplays.zip`, `Videos.zip`, `mp3s.zip`, `mkv.zip`, `Trailer.zip` | `data/extras/<name>` |
| `Photos.zip`, `Type-Ins.zip` | `data/extras/<name>` (not referenced by the database) |
| `Music.zip` (optional, HVSC with `GAMES`, `MUSICIANS`, `DEMOS`) | `data/music` |

You don't need every zip. Missing ones are skipped, and the related files show up as missing in the app.

### 2. Extract them

**From the app:** click **Populate folders…**, optionally pick a different *Data folder* and *Sources folder*, click **Create Folder Structure**, then **Populate folders**.

**From the command line:**

```sh
python populate.py --dry-run   # show what would be extracted
python populate.py             # extract
python data_audit.py           # just create the folder tree
```

Re-running is safe. Files that already exist with the same size are skipped, and unsafe zip paths are ignored. Names are matched case-insensitively and ignore macOS/Windows Unicode differences.

## Settings

Open **Settings…** from the main window. Everything is saved in `config.json` next to the app.

| Setting | What it does |
| --- | --- |
| **Controller** | VICE joystick device for port 2: numpad keys, VICE keyset 1, or a real joystick/gamepad. |
| **VICE executable** | Path to `x64sc`, its folder or `x64sc.app`. If empty, the app searches `VICE_PATH`, the saved setting, `data/vice`, your `PATH`, and the usual install locations. |
| **Extra arguments** | Added to the VICE command line at every launch. |
| **Data folder** | Point the app at a data folder elsewhere, for example on an external drive. |

## Building a standalone app

```sh
pip install pyinstaller pillow
python build.py
```

The database and `data/vice` are copied next to the app in `dist/`. The large game data folder is chosen in Settings, or placed next to the app as `data/`.


## Credits

The start-up photo (`images/c64.jpg`) is [Commodore64.jpg](https://commons.wikimedia.org/wiki/File:Commodore64.jpg) from Wikimedia Commons, licensed [CC BY-SA 2.5](https://creativecommons.org/licenses/by-sa/2.5/), resized.
