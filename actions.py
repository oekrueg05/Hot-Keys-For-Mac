"""Action handlers for hotkey triggers."""

import logging
import shlex
import subprocess
from typing import Optional

from pynput.keyboard import Controller

logger = logging.getLogger("hotkeys")

_keyboard = Controller()
_warned_no_appkit = False


def run_app(target: str) -> None:
    subprocess.Popen(["open", "-a", target])


def run_shell(target: str) -> None:
    subprocess.Popen(shlex.split(target))


def run_text(target: str) -> None:
    _keyboard.type(target)


def run_applescript(target: str) -> None:
    subprocess.Popen(["osascript", "-e", target])


HANDLERS = {
    "app": run_app,
    "shell": run_shell,
    "text": run_text,
    "applescript": run_applescript,
}


def frontmost_app_name() -> Optional[str]:
    """Localized name of the frontmost app, or None if pyobjc's AppKit isn't installed."""
    global _warned_no_appkit
    try:
        from AppKit import NSWorkspace
    except ImportError:
        if not _warned_no_appkit:
            logger.warning(
                "app_scope requires pyobjc-framework-Cocoa; install it to use scoped hotkeys."
            )
            _warned_no_appkit = True
        return None

    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return app.localizedName() if app else None


def dispatch(name: str, action: dict) -> None:
    action_type = action.get("type")
    target = action.get("target")
    app_scope = action.get("app_scope")

    if app_scope:
        frontmost = frontmost_app_name()
        if frontmost != app_scope:
            logger.debug(
                "Skipping %r: frontmost app is %r, not %r", name, frontmost, app_scope
            )
            return

    handler = HANDLERS.get(action_type)
    if handler is None:
        logger.error("Unknown action type %r for hotkey %r", action_type, name)
        return

    logger.info("Triggered %r -> %s(%r)", name, action_type, target)
    try:
        handler(target)
    except Exception:
        logger.exception("Action failed for hotkey %r", name)
