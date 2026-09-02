#!/usr/bin/env python3
"""Menu bar wrapper (rumps) around the global hotkey listener, with start/stop/status."""

import logging
import os

import rumps
from pynput import keyboard

import main as hotkeys_main

logger = logging.getLogger("hotkeys")

ICON_ON = "⌨"
ICON_OFF = "⌨ (off)"


class HotkeysApp(rumps.App):
    def __init__(self, config_path=hotkeys_main.DEFAULT_CONFIG_PATH):
        super().__init__("Hotkeys", title=ICON_ON, quit_button=None)
        self.config_path = config_path
        self.listener = None
        self.last_mtime = None

        self.active_item = rumps.MenuItem("Active", callback=self.toggle_active)
        self.reload_item = rumps.MenuItem("Reload Config", callback=self.reload_config)
        self.quit_item = rumps.MenuItem("Quit", callback=self.quit_app)
        self.menu = [self.active_item, self.reload_item, None, self.quit_item]

        hotkeys_main.check_accessibility_permission()
        self.start_listener()

        self.timer = rumps.Timer(self.check_for_reload, hotkeys_main.RELOAD_CHECK_INTERVAL)
        self.timer.start()

    def start_listener(self) -> None:
        config = hotkeys_main.load_config(self.config_path)
        hotkey_map = hotkeys_main.make_hotkey_map(config)
        self.listener = keyboard.GlobalHotKeys(hotkey_map)
        self.listener.start()
        self.last_mtime = os.path.getmtime(self.config_path)
        self.active_item.state = True
        self.title = ICON_ON
        logger.info("Listener started with %d hotkey(s)", len(config))

    def stop_listener(self) -> None:
        if self.listener is not None:
            self.listener.stop()
            self.listener = None
        self.active_item.state = False
        self.title = ICON_OFF
        logger.info("Listener stopped")

    def toggle_active(self, sender) -> None:
        if self.listener is None:
            self.start_listener()
        else:
            self.stop_listener()

    def reload_config(self, sender) -> None:
        was_active = self.listener is not None
        if was_active:
            self.stop_listener()
        try:
            if was_active:
                self.start_listener()
            else:
                self.last_mtime = os.path.getmtime(self.config_path)
        except (OSError, ValueError) as e:
            logger.error("Failed to reload config: %s", e)
            rumps.alert("Failed to reload config", str(e))

    def check_for_reload(self, _timer) -> None:
        if self.listener is None:
            return
        try:
            mtime = os.path.getmtime(self.config_path)
        except OSError:
            return
        if mtime != self.last_mtime:
            logger.info("Config change detected, reloading %s", self.config_path)
            self.stop_listener()
            try:
                self.start_listener()
            except (OSError, ValueError) as e:
                logger.error("Failed to reload config: %s", e)

    def quit_app(self, sender) -> None:
        self.stop_listener()
        rumps.quit_application()


def main() -> None:
    hotkeys_main.setup_logging()
    HotkeysApp().run()


if __name__ == "__main__":
    main()
