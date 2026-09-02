# Hot-Keys

A lightweight background app for macOS that lets you define global keyboard shortcuts, each triggering a custom action (open an app, run a shell command, type text, or run AppleScript/VBA), optionally scoped to only fire when a specific app — e.g. Microsoft Excel — is frontmost.

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`pyobjc-framework-Quartz` is optional — it's only used to detect whether Accessibility permission is granted and print a helpful message. `pyobjc-framework-Cocoa` is optional too — it's only needed for `app_scope` (below). The app still runs without either.

## Configure hotkeys

Edit `hotkeys.json`. Keys use `pynput`'s hotkey syntax (modifiers wrapped in `<...>`, joined with `+`):

```json
{
  "<cmd>+<shift>+j": {"type": "app", "target": "Notes"},
  "<cmd>+<shift>+k": {"type": "shell", "target": "say hello"},
  "<cmd>+<shift>+l": {"type": "text", "target": "hello@email.com"},
  "<cmd>+<shift>+u": {
    "type": "applescript",
    "target": "tell application \"Microsoft Excel\" to set value of active cell to \"=SUM(A1:A10)\"",
    "app_scope": "Microsoft Excel"
  }
}
```

Action types:
- `app` — opens `target` with `open -a "<target>"`
- `shell` — runs `target` as a command (parsed with `shlex`, no shell interpolation — pipes/redirects won't work)
- `text` — types `target` out via the keyboard controller
- `applescript` — runs `target` as an AppleScript via `osascript`. This is how to drive Excel directly: set cell values/formulas, run a VBA macro (`tell application "Microsoft Excel" to run VBA macro "MacroName"`), navigate sheets, etc. — anything in Excel's AppleScript dictionary.

**`app_scope`** (optional, any action type): the hotkey only fires when the named app (its localized name, e.g. `"Microsoft Excel"`) is frontmost. If another app is frontmost, the keystroke is ignored by this tool and passes through untouched — so scoped hotkeys won't hijack the same shortcut in other apps. Requires `pyobjc-framework-Cocoa`; without it, scoped hotkeys log a warning and never fire.

Editing `hotkeys.json` while the app is running is picked up automatically within a couple seconds (no restart needed).

## Grant Accessibility permission

macOS requires Accessibility access to listen for global hotkeys and simulate keystrokes:

1. Open **System Settings → Privacy & Security → Accessibility**
2. Enable access for whichever process runs the script (usually **Terminal**, or **iTerm** if that's what you use)
3. Run the app

If `pyobjc-framework-Quartz` is installed, the app checks this on startup and prints instructions if permission is missing.

## Run

```bash
python3 main.py
```

Or with a different config:

```bash
python3 main.py -c /path/to/other-hotkeys.json
```

Logs are written to `hotkeys.log` and echoed to stdout. Stop with `Ctrl+C`.

## Edit hotkeys with a GUI (optional)

```bash
python3 config_editor.py
```

A small Tkinter window listing all configured hotkeys, with **Add**, **Edit** (or double-click a row), **Delete**, and **Save**. Hotkey syntax is validated with `pynput`'s own parser before it's saved, so you can't write a combo the listener can't load. It edits `hotkeys.json` directly — if `main.py` or `menubar.py` is already running, saving here triggers their normal hot-reload within a couple seconds.

Tkinter ships with the python.org installer; on Homebrew Python you may need `brew install python-tk`.

## Run as a menu bar app (optional)

```bash
python3 menubar.py
```

Shows a keyboard icon in the menu bar with:
- **Active** — checkbox toggle to start/stop the listener without quitting
- **Reload Config** — manually re-read `hotkeys.json`
- **Quit**

The icon label switches to "(off)" while stopped. Config hot-reload (via the same file-watch as `main.py`) still applies whenever the listener is active.

## Auto-start at login (optional)

```bash
./install_launch_agent.sh          # installs menubar.py as the login item
./install_launch_agent.sh main.py  # or install main.py (no menu bar) instead
```

This generates `~/Library/LaunchAgents/com.hotkeys.menubar.plist` from `com.hotkeys.menubar.plist.template` (using your venv's Python if `venv/` exists, otherwise whatever `python3` is on `PATH`), then loads it with `launchctl`. The app now starts automatically at login and restarts itself if it crashes (but not if you quit it deliberately via the menu bar or `Ctrl+C`). Output is logged to `launchd.out.log` / `launchd.err.log` in this directory.

To remove it:

```bash
launchctl unload ~/Library/LaunchAgents/com.hotkeys.menubar.plist
rm ~/Library/LaunchAgents/com.hotkeys.menubar.plist
```
