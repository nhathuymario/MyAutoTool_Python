from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import AutoToolApp


class AppLogger:
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget

    def __call__(self, message: str) -> None:
        self.text_widget.insert("end", message + "\n")
        self.text_widget.see("end")
        self.text_widget.update_idletasks()


class AutoToolUI:
    def __init__(self, app: "AutoToolApp"):
        self.app = app
        self.root = app.root

    def build(self) -> tk.Text:
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        left = tk.Frame(main_frame, bg="#f4f4f4", width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(main_frame, bg="white")
        right.pack(side="right", fill="both", expand=True)

        tk.Label(
            left,
            text="MENU CHỨC NĂNG",
            font=("Arial", 16, "bold"),
            bg="#f4f4f4"
        ).pack(anchor="w", padx=12, pady=(12, 6))

        self._build_group_ldplayer(left)
        self._build_group_game(left)
        self._build_group_bot(left)
        self._build_group_settings(left)

        tk.Label(
            right,
            text="LOG HỆ THỐNG",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(anchor="w", padx=12, pady=(12, 6))

        status_frame = tk.Frame(right, bg="white")
        status_frame.pack(fill="x", padx=12)

        tk.Label(
            status_frame,
            text="ADB Device:",
            bg="white",
            font=("Arial", 10, "bold")
        ).pack(side="left")

        tk.Label(
            status_frame,
            textvariable=self.app.var_device_id,
            bg="white",
            fg="blue"
        ).pack(side="left", padx=(6, 0))

        log_box = tk.Text(right, wrap="word", font=("Consolas", 10))
        log_box.pack(fill="both", expand=True, padx=12, pady=12)
        return log_box

    def _make_group(self, parent, title: str) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill="x", padx=10, pady=6)
        return frame

    def _build_group_ldplayer(self, parent) -> None:
        frame = self._make_group(parent, "LDPlayer")
        ttk.Button(frame, text="Open LDPlayer", command=self.app.handle_open_ldplayer).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Focus LDPlayer", command=self.app.handle_focus_ldplayer).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="List Instances", command=self.app.handle_list_instances).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Connect ADB", command=self.app.handle_connect_adb).pack(fill="x", padx=8, pady=4)

    def _build_group_game(self, parent) -> None:
        frame = self._make_group(parent, "Game")
        ttk.Button(frame, text="Open Game by Package", command=self.app.handle_open_game_by_package).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Open Game by Icon", command=self.app.handle_open_game_by_icon).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Save Screenshot", command=self.app.handle_save_screenshot).pack(fill="x", padx=8, pady=4)

        # ttk.Button(frame, text="Test Battle", command=lambda: self.app.handle_test_template("battle", "Battle")).pack(fill="x", padx=8, pady=4)
        # ttk.Button(frame, text="Test Ready", command=lambda: self.app.handle_test_template("ready", "Ready")).pack(fill="x", padx=8, pady=4)
        # ttk.Button(frame, text="Test Victory", command=lambda: self.app.handle_test_template("victory", "Victory")).pack(fill="x", padx=8, pady=4)
        # ttk.Button(frame, text="Test Next Stage", command=lambda: self.app.handle_test_template("next_stage", "Next Stage")).pack(fill="x", padx=8, pady=4)
        # ttk.Button(frame, text="Test Skip", command=lambda: self.app.handle_test_template("skip", "Skip")).pack(fill="x", padx=8, pady=4)

    def _build_group_bot(self, parent) -> None:
        frame = self._make_group(parent, "Bot")
        ttk.Button(frame, text="Start Bot", command=self.app.handle_start_bot).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Stop Bot", command=self.app.handle_stop_bot).pack(fill="x", padx=8, pady=4)

    def _build_group_settings(self, parent) -> None:
        frame = self._make_group(parent, "Cài đặt")
        self._entry_row(frame, "LDPlayer Path", self.app.var_ldplayer_path)
        self._entry_row(frame, "ADB Path", self.app.var_adb_path)
        self._entry_row(frame, "LDConsole", self.app.var_ldconsole_path)
        self._entry_row(frame, "Image Dir", self.app.var_image_dir)
        self._entry_row(frame, "Game Package", self.app.var_game_package)
        self._entry_row(frame, "Game Activity", self.app.var_game_activity)
        self._entry_row(frame, "Region", self.app.var_scan_region)
        self._entry_row(frame, "Threshold", self.app.var_threshold)
        self._entry_row(frame, "Loop Delay", self.app.var_loop_delay)
        self._entry_row(frame, "Action Delay", self.app.var_action_delay)
        ttk.Button(frame, text="Save Config", command=self.app.handle_save_config).pack(fill="x", padx=8, pady=8)

    def _entry_row(self, parent, label: str, variable) -> None:
        row = tk.Frame(parent)
        row.pack(fill="x", padx=8, pady=2)

        tk.Label(row, text=label, width=12, anchor="w").pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True)