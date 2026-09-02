# Hot-Keys

A lightweight background app for macOS that lets you define global keyboard shortcuts, each triggering a custom action (open an app, run a shell command, or type text).

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`pyobjc-framework-Quartz` is optional — it's only used to detect whether Accessibility permission is granted and print a helpful message. The app still runs without it.

## Configure hotkeys

Edit `hotkeys.json`. Keys use `pynput`'s hotkey syntax (modifiers wrapped in `<...>`, joined with `+`):

```json
{
  "<cmd>+<shift>+j": {"type": "app", "target": "Notes"},
  "<cmd>+<shift>+k": {"type": "shell", "target": "say hello"},
  "<cmd>+<shift>+l": {"type": "text", "target": "hello@email.com"}
}
```

Action types:
- `app` — opens `target` with `open -a "<target>"`
- `shell` — runs `target` as a command (parsed with `shlex`, no shell interpolation — pipes/redirects won't work)
- `text` — types `target` out via the keyboard controller

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

To run automatically on login, create a `launchd` plist in `~/Library/LaunchAgents/` pointing at your venv's Python and `main.py`, then load it with `launchctl load ~/Library/LaunchAgents/<name>.plist`.
