#!/usr/bin/env python3
"""Global hotkey listener for macOS. Loads hotkeys.json and dispatches actions."""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from pynput import keyboard

import actions

DEFAULT_CONFIG_PATH = Path(__file__).parent / "hotkeys.json"
LOG_PATH = Path(__file__).parent / "hotkeys.log"
RELOAD_CHECK_INTERVAL = 2  # seconds


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def make_hotkey_map(config: dict) -> dict:
    hotkey_map = {}
    for name, action in config.items():
        def handler(action=action, name=name):
            actions.dispatch(name, action)
        hotkey_map[name] = handler
    return hotkey_map


def check_accessibility_permission() -> None:
    """Best-effort check for macOS Accessibility permission (requires pyobjc)."""
    try:
        from Quartz import CGPreflightListenEventAccess
    except ImportError:
        return

    if not CGPreflightListenEventAccess():
        print(
            "\nAccessibility permission is not granted to this process.\n"
            "Global hotkeys will not work until you enable it:\n"
            "  1. Open System Settings -> Privacy & Security -> Accessibility\n"
            "  2. Enable access for Terminal (or the Python binary running this script)\n"
            "  3. Re-run this script\n",
            file=sys.stderr,
        )


def run(config_path: Path) -> None:
    setup_logging()
    logger = logging.getLogger("hotkeys")

    check_accessibility_permission()

    config = load_config(config_path)
    logger.info("Loaded %d hotkey(s) from %s", len(config), config_path)

    last_mtime = os.path.getmtime(config_path)
    listener_holder = {}

    def start_listener(cfg: dict) -> keyboard.GlobalHotKeys:
        hotkey_map = make_hotkey_map(cfg)
        listener = keyboard.GlobalHotKeys(hotkey_map)
        listener.start()
        return listener

    listener_holder["listener"] = start_listener(config)

    try:
        while True:
            time.sleep(RELOAD_CHECK_INTERVAL)
            try:
                mtime = os.path.getmtime(config_path)
            except OSError:
                continue
            if mtime != last_mtime:
                logger.info("Config change detected, reloading %s", config_path)
                try:
                    new_config = load_config(config_path)
                except (json.JSONDecodeError, OSError) as e:
                    logger.error("Failed to reload config: %s", e)
                    continue
                listener_holder["listener"].stop()
                listener_holder["listener"] = start_listener(new_config)
                config = new_config
                last_mtime = mtime
    except KeyboardInterrupt:
        logger.info("Shutting down.")
        listener_holder["listener"].stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Global hotkey listener for macOS")
    parser.add_argument(
        "-c", "--config", type=Path, default=DEFAULT_CONFIG_PATH,
        help="Path to hotkeys config file (default: hotkeys.json)",
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    run(args.config)


if __name__ == "__main__":
    main()
