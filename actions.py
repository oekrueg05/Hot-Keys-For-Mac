"""Action handlers for hotkey triggers."""

import logging
import shlex
import subprocess

from pynput.keyboard import Controller

logger = logging.getLogger("hotkeys")

_keyboard = Controller()


def run_app(target: str) -> None:
    subprocess.Popen(["open", "-a", target])


def run_shell(target: str) -> None:
    subprocess.Popen(shlex.split(target))


def run_text(target: str) -> None:
    _keyboard.type(target)


HANDLERS = {
    "app": run_app,
    "shell": run_shell,
    "text": run_text,
}


def dispatch(name: str, action: dict) -> None:
    action_type = action.get("type")
    target = action.get("target")
    handler = HANDLERS.get(action_type)

    if handler is None:
        logger.error("Unknown action type %r for hotkey %r", action_type, name)
        return

    logger.info("Triggered %r -> %s(%r)", name, action_type, target)
    try:
        handler(target)
    except Exception:
        logger.exception("Action failed for hotkey %r", name)
