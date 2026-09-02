#!/usr/bin/env python3
"""Tkinter GUI for adding/editing/deleting hotkeys.json entries without hand-editing JSON."""

import argparse
import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from pynput.keyboard import HotKey

from actions import HANDLERS

ACTION_TYPES = list(HANDLERS.keys())
DEFAULT_CONFIG_PATH = Path(__file__).parent / "hotkeys.json"


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_config(path: Path, config: dict) -> None:
    with open(path, "w") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


class EntryDialog(tk.Toplevel):
    """Modal dialog for adding or editing a single hotkey entry."""

    def __init__(self, parent, hotkey="", action=None):
        super().__init__(parent)
        self.title("Edit hotkey" if hotkey else "Add hotkey")
        self.result = None
        action = action or {}

        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        pad = {"padx": 8, "pady": 4}

        tk.Label(self, text="Hotkey (e.g. <cmd>+<shift>+j)").grid(row=0, column=0, sticky="w", **pad)
        self.hotkey_var = tk.StringVar(value=hotkey)
        tk.Entry(self, textvariable=self.hotkey_var, width=42).grid(row=0, column=1, **pad)

        tk.Label(self, text="Type").grid(row=1, column=0, sticky="w", **pad)
        self.type_var = tk.StringVar(value=action.get("type", ACTION_TYPES[0]))
        ttk.Combobox(
            self, textvariable=self.type_var, values=ACTION_TYPES, state="readonly", width=39
        ).grid(row=1, column=1, **pad)

        tk.Label(self, text="Target").grid(row=2, column=0, sticky="nw", **pad)
        self.target_text = tk.Text(self, width=42, height=5)
        self.target_text.insert("1.0", action.get("target", ""))
        self.target_text.grid(row=2, column=1, **pad)

        tk.Label(self, text="App scope (optional)").grid(row=3, column=0, sticky="w", **pad)
        self.scope_var = tk.StringVar(value=action.get("app_scope", ""))
        tk.Entry(self, textvariable=self.scope_var, width=42).grid(row=3, column=1, **pad)
        tk.Label(
            self, text="e.g. Microsoft Excel — only fires when that app is frontmost",
            fg="gray",
        ).grid(row=4, column=1, sticky="w", padx=8)

        btns = tk.Frame(self)
        btns.grid(row=5, column=0, columnspan=2, pady=8)
        tk.Button(btns, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        tk.Button(btns, text="Save", command=self._on_save).pack(side="left", padx=4)

        self.bind("<Escape>", lambda e: self.destroy())

    def _on_save(self):
        hotkey = self.hotkey_var.get().strip()
        action_type = self.type_var.get().strip()
        target = self.target_text.get("1.0", "end").strip()
        app_scope = self.scope_var.get().strip()

        if not hotkey:
            messagebox.showerror("Invalid entry", "Hotkey cannot be empty.", parent=self)
            return
        try:
            HotKey.parse(hotkey)
        except (ValueError, KeyError) as e:
            messagebox.showerror("Invalid hotkey", f"Could not parse {hotkey!r}: {e}", parent=self)
            return
        if not target:
            messagebox.showerror("Invalid entry", "Target cannot be empty.", parent=self)
            return

        action = {"type": action_type, "target": target}
        if app_scope:
            action["app_scope"] = app_scope

        self.result = (hotkey, action)
        self.destroy()


class ConfigEditor(tk.Tk):
    def __init__(self, config_path: Path):
        super().__init__()
        self.config_path = config_path
        self.config = load_config(config_path)

        self.title(f"Hot-Keys Config Editor — {config_path}")
        self.geometry("680x380")

        columns = ("hotkey", "type", "target", "app_scope")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        for col, width in zip(columns, (160, 90, 280, 130)):
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        btns = tk.Frame(self)
        btns.pack(fill="x", padx=8, pady=(0, 8))
        tk.Button(btns, text="Add", command=self.add_entry).pack(side="left")
        tk.Button(btns, text="Edit", command=self.edit_selected).pack(side="left", padx=4)
        tk.Button(btns, text="Delete", command=self.delete_selected).pack(side="left")
        tk.Button(btns, text="Reload from disk", command=self.reload).pack(side="left", padx=4)
        tk.Button(btns, text="Save", command=self.save).pack(side="right")

        self.status_var = tk.StringVar()
        tk.Label(self, textvariable=self.status_var, anchor="w").pack(fill="x", padx=8, pady=(0, 8))

        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for hotkey, action in self.config.items():
            target = action.get("target", "")
            preview = target if len(target) <= 60 else target[:57] + "..."
            self.tree.insert(
                "", "end", iid=hotkey,
                values=(hotkey, action.get("type", ""), preview, action.get("app_scope", "")),
            )
        dirty = " (unsaved changes)" if self._dirty() else ""
        self.status_var.set(f"{len(self.config)} hotkey(s){dirty}")

    def _dirty(self) -> bool:
        return self.config != load_config(self.config_path)

    def add_entry(self):
        dialog = EntryDialog(self)
        self.wait_window(dialog)
        if dialog.result is None:
            return
        hotkey, action = dialog.result
        if hotkey in self.config and not messagebox.askyesno(
            "Overwrite?", f"{hotkey!r} already exists. Overwrite it?"
        ):
            return
        self.config[hotkey] = action
        self._refresh_tree()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        old_hotkey = selected[0]
        dialog = EntryDialog(self, hotkey=old_hotkey, action=self.config[old_hotkey])
        self.wait_window(dialog)
        if dialog.result is None:
            return
        new_hotkey, action = dialog.result
        if new_hotkey != old_hotkey:
            del self.config[old_hotkey]
        self.config[new_hotkey] = action
        self._refresh_tree()

    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        hotkey = selected[0]
        if messagebox.askyesno("Delete", f"Delete hotkey {hotkey!r}?"):
            del self.config[hotkey]
            self._refresh_tree()

    def reload(self):
        if self._dirty() and not messagebox.askyesno(
            "Discard changes?", "Reloading will discard unsaved changes. Continue?"
        ):
            return
        self.config = load_config(self.config_path)
        self._refresh_tree()

    def save(self):
        try:
            save_config(self.config_path, self.config)
        except OSError as e:
            messagebox.showerror("Save failed", str(e))
            return
        self._refresh_tree()


def main():
    parser = argparse.ArgumentParser(description="GUI editor for hotkeys.json")
    parser.add_argument(
        "-c", "--config", type=Path, default=DEFAULT_CONFIG_PATH,
        help="Path to hotkeys config file (default: hotkeys.json)",
    )
    args = parser.parse_args()
    ConfigEditor(args.config).mainloop()


if __name__ == "__main__":
    main()
