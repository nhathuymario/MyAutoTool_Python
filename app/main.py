from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, Optional, Tuple

from .adb_client import AdbClient
from .bot import BotSettings, GameBot
from .config_manager import BASE_DIR, load_config, resolve_path, save_config
from .image_matcher import ImageMatcher
from .ldplayer import LDPlayerController


class AppLogger:
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget

    def __call__(self, message: str) -> None:
        self.text_widget.insert("end", message + "\n")
        self.text_widget.see("end")
        self.text_widget.update_idletasks()


class AutoToolApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LDPlayer Auto Tool")
        self.root.geometry("1100x700")
        self.root.minsize(980, 620)

        self.config = load_config()
        self.log_box: Optional[tk.Text] = None
        self.logger: Optional[AppLogger] = None

        self.var_ldplayer_path = tk.StringVar(value=self.config["ldplayer_path"])
        self.var_adb_path = tk.StringVar(value=self.config["adb_path"])
        self.var_game_package = tk.StringVar(value=self.config.get("game_package", ""))
        self.var_game_activity = tk.StringVar(value=self.config.get("game_activity", ""))
        self.var_threshold = tk.DoubleVar(value=float(self.config.get("default_threshold", 0.75)))
        self.var_loop_delay = tk.DoubleVar(value=float(self.config.get("loop_delay_seconds", 1.0)))
        self.var_action_delay = tk.DoubleVar(value=float(self.config.get("action_delay_seconds", 0.35)))
        self.var_scan_region = tk.StringVar(value=self.region_to_string(self.config.get("scan_region")))
        self.var_device_id = tk.StringVar(value="Chưa kết nối")
        self.var_feature_build = tk.BooleanVar(value=bool(self.config["features"].get("build", True)))
        self.var_feature_collect = tk.BooleanVar(value=bool(self.config["features"].get("collect", True)))
        self.var_feature_upgrade = tk.BooleanVar(value=bool(self.config["features"].get("upgrade", True)))

        self._build_ui()

        self.logger = AppLogger(self.log_box)
        self.matcher = ImageMatcher()
        self.adb = AdbClient(
            adb_path=self.var_adb_path.get(),
            device_ip=self.config.get("device_ip", "127.0.0.1"),
            candidate_ports=self.config.get("candidate_ports", [5555, 5556, 5557]),
            logger=self.logger,
        )
        self.ldplayer = LDPlayerController(
            ldplayer_path=self.var_ldplayer_path.get(),
            ldconsole_path=self.config.get("ldconsole_path", ""),
            title_keywords=self.config.get("window_title_keywords", ["LDPlayer"]),
            logger=self.logger,
        )
        self.bot = GameBot(self.adb, self.matcher, logger=self.logger)

        self.logger("Tool đã sẵn sàng.")
        self.logger(f"Thư mục project: {BASE_DIR}")

    @staticmethod
    def region_to_string(region) -> str:
        if region is None:
            return ""
        return ",".join(str(int(v)) for v in region)

    @staticmethod
    def parse_region(text: str) -> Optional[Tuple[int, int, int, int]]:
        text = text.strip()
        if not text:
            return None
        parts = [p.strip() for p in text.split(",")]
        if len(parts) != 4:
            raise ValueError("Region phải có dạng left,top,width,height")
        values = tuple(int(p) for p in parts)
        if values[2] <= 0 or values[3] <= 0:
            raise ValueError("width và height phải > 0")
        return values

    def _build_ui(self) -> None:
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        left = tk.Frame(main_frame, bg="#f4f4f4", width=340)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(main_frame, bg="white")
        right.pack(side="right", fill="both", expand=True)

        tk.Label(left, text="MENU CHỨC NĂNG", font=("Arial", 16, "bold"), bg="#f4f4f4").pack(anchor="w", padx=12, pady=(12, 6))

        self._build_group_ldplayer(left)
        self._build_group_game(left)
        self._build_group_bot(left)
        self._build_group_settings(left)

        tk.Label(right, text="LOG HỆ THỐNG", font=("Arial", 14, "bold"), bg="white").pack(anchor="w", padx=12, pady=(12, 6))
        status_frame = tk.Frame(right, bg="white")
        status_frame.pack(fill="x", padx=12)
        tk.Label(status_frame, text="ADB Device:", bg="white", font=("Arial", 10, "bold")).pack(side="left")
        tk.Label(status_frame, textvariable=self.var_device_id, bg="white", fg="blue").pack(side="left", padx=(6, 0))

        self.log_box = tk.Text(right, wrap="word", font=("Consolas", 10))
        self.log_box.pack(fill="both", expand=True, padx=12, pady=12)

    def _make_group(self, parent, title: str) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(parent, text=title)
        frame.pack(fill="x", padx=10, pady=6)
        return frame

    def _build_group_ldplayer(self, parent) -> None:
        frame = self._make_group(parent, "LDPlayer")
        ttk.Button(frame, text="Open LDPlayer", command=self.handle_open_ldplayer).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Focus LDPlayer", command=self.handle_focus_ldplayer).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="List Instances", command=self.handle_list_instances).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Connect ADB", command=self.handle_connect_adb).pack(fill="x", padx=8, pady=4)

    def _build_group_game(self, parent) -> None:
        frame = self._make_group(parent, "Game")
        ttk.Button(frame, text="Open Game by Package", command=self.handle_open_game_by_package).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Open Game by Icon", command=self.handle_open_game_by_icon).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Save Screenshot", command=self.handle_save_screenshot).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Test Build", command=lambda: self.handle_test_template("build", "Build")).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Test Collect", command=lambda: self.handle_test_template("collect", "Collect")).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Test Upgrade", command=lambda: self.handle_test_template("upgrade", "Upgrade")).pack(fill="x", padx=8, pady=4)

    def _build_group_bot(self, parent) -> None:
        frame = self._make_group(parent, "Bot")
        ttk.Checkbutton(frame, text="Auto Build", variable=self.var_feature_build).pack(anchor="w", padx=8, pady=2)
        ttk.Checkbutton(frame, text="Auto Collect", variable=self.var_feature_collect).pack(anchor="w", padx=8, pady=2)
        ttk.Checkbutton(frame, text="Auto Upgrade", variable=self.var_feature_upgrade).pack(anchor="w", padx=8, pady=2)
        ttk.Button(frame, text="Start Bot", command=self.handle_start_bot).pack(fill="x", padx=8, pady=4)
        ttk.Button(frame, text="Stop Bot", command=self.handle_stop_bot).pack(fill="x", padx=8, pady=4)

    def _build_group_settings(self, parent) -> None:
        frame = self._make_group(parent, "Cài đặt")
        self._entry_row(frame, "LDPlayer Path", self.var_ldplayer_path)
        self._entry_row(frame, "ADB Path", self.var_adb_path)
        self._entry_row(frame, "Game Package", self.var_game_package)
        self._entry_row(frame, "Game Activity", self.var_game_activity)
        self._entry_row(frame, "Region", self.var_scan_region)
        self._entry_row(frame, "Threshold", self.var_threshold)
        self._entry_row(frame, "Loop Delay", self.var_loop_delay)
        self._entry_row(frame, "Action Delay", self.var_action_delay)
        ttk.Button(frame, text="Save Config", command=self.handle_save_config).pack(fill="x", padx=8, pady=8)

    def _entry_row(self, parent, label: str, variable) -> None:
        row = tk.Frame(parent)
        row.pack(fill="x", padx=8, pady=2)
        tk.Label(row, text=label, width=12, anchor="w").pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True)

    def sync_runtime_paths(self) -> None:
        self.ldplayer.ldplayer_path = self.var_ldplayer_path.get().strip()
        self.adb.adb_path = self.var_adb_path.get().strip()

    def handle_open_ldplayer(self) -> None:
        self.sync_runtime_paths()
        ok = self.ldplayer.open_ldplayer()
        if ok:
            self.ldplayer.wait_boot(10)

    def handle_focus_ldplayer(self) -> None:
        self.ldplayer.focus_window()

    def handle_list_instances(self) -> None:
        self.ldplayer.list_instances()

    def handle_connect_adb(self) -> None:
        self.sync_runtime_paths()
        device = self.adb.auto_connect()
        self.var_device_id.set(device or "Chưa kết nối")

    def ensure_connected(self) -> bool:
        if self.adb.device_id:
            self.var_device_id.set(self.adb.device_id)
            return True
        self.handle_connect_adb()
        return bool(self.adb.device_id)

    def handle_open_game_by_package(self) -> None:
        if not self.ensure_connected():
            return
        package_name = self.var_game_package.get().strip()
        activity = self.var_game_activity.get().strip()
        try:
            self.adb.start_app(package_name, activity)
        except Exception as exc:
            self.logger(f"[Game] Lỗi mở game bằng package: {exc}")

    def handle_open_game_by_icon(self) -> None:
        if not self.ensure_connected():
            return
        try:
            screen = self.adb.screencap()
            template_path = self.config["templates"]["game_icon"]
            match = self.matcher.find_template(
                screen_bgr=screen,
                template_path=template_path,
                threshold=float(self.var_threshold.get()),
                region=self.safe_region(),
            )
            if not match:
                self.logger("[Game] Không tìm thấy game_icon.png")
                return
            self.adb.tap(match.x, match.y)
            preview = self.matcher.save_match_preview(screen, match, prefix="game_icon")
            self.logger(f"[Game] Đã click icon game tại ({match.x}, {match.y}) score={match.score:.3f}")
            self.logger(f"[Game] Preview: {preview}")
        except Exception as exc:
            self.logger(f"[Game] Lỗi mở game bằng icon: {exc}")

    def handle_save_screenshot(self) -> None:
        if not self.ensure_connected():
            return
        try:
            screen = self.adb.screencap()
            path = self.matcher.save_debug_image(screen, prefix="manual_capture")
            self.logger(f"[Debug] Đã lưu screenshot: {path}")
        except Exception as exc:
            self.logger(f"[Debug] Lỗi screenshot: {exc}")

    def handle_test_template(self, key: str, label: str) -> None:
        if not self.ensure_connected():
            return
        try:
            screen = self.adb.screencap()
            match = self.matcher.find_template(
                screen_bgr=screen,
                template_path=self.config["templates"][key],
                threshold=float(self.var_threshold.get()),
                region=self.safe_region(),
            )
            if not match:
                self.logger(f"[{label}] Not found")
                save_path = self.matcher.save_debug_image(screen, prefix=f"{key}_notfound")
                self.logger(f"[{label}] Saved screen: {save_path}")
                return
            preview = self.matcher.save_match_preview(screen, match, prefix=key)
            self.logger(f"[{label}] Found at ({match.x}, {match.y}) score={match.score:.3f}")
            self.logger(f"[{label}] Preview: {preview}")
        except Exception as exc:
            self.logger(f"[{label}] Error: {exc}")

    def handle_start_bot(self) -> None:
        if not self.ensure_connected():
            return
        try:
            settings = BotSettings(
                threshold=float(self.var_threshold.get()),
                loop_delay_seconds=float(self.var_loop_delay.get()),
                action_delay_seconds=float(self.var_action_delay.get()),
                scan_region=self.safe_region(),
                auto_reconnect=bool(self.config.get("auto_reconnect", True)),
                features={
                    "build": self.var_feature_build.get(),
                    "collect": self.var_feature_collect.get(),
                    "upgrade": self.var_feature_upgrade.get(),
                },
                templates=self.config["templates"],
            )
            started = self.bot.start(settings)
            if started:
                self.var_device_id.set(self.adb.device_id or "Chưa kết nối")
        except Exception as exc:
            self.logger(f"[Bot] Không start được: {exc}")

    def handle_stop_bot(self) -> None:
        self.bot.stop()

    def safe_region(self) -> Optional[Tuple[int, int, int, int]]:
        return self.parse_region(self.var_scan_region.get())

    def handle_save_config(self) -> None:
        try:
            region = self.safe_region()
            self.config["ldplayer_path"] = self.var_ldplayer_path.get().strip()
            self.config["adb_path"] = self.var_adb_path.get().strip()
            self.config["game_package"] = self.var_game_package.get().strip()
            self.config["game_activity"] = self.var_game_activity.get().strip()
            self.config["default_threshold"] = float(self.var_threshold.get())
            self.config["loop_delay_seconds"] = float(self.var_loop_delay.get())
            self.config["action_delay_seconds"] = float(self.var_action_delay.get())
            self.config["scan_region"] = list(region) if region else None
            self.config["features"] = {
                "build": self.var_feature_build.get(),
                "collect": self.var_feature_collect.get(),
                "upgrade": self.var_feature_upgrade.get(),
            }
            save_config(self.config)
            self.logger("[Config] Đã lưu config.json")
            self.sync_runtime_paths()
        except Exception as exc:
            messagebox.showerror("Lỗi cấu hình", str(exc))


def run_app() -> None:
    root = tk.Tk()
    app = AutoToolApp(root)

    def on_close() -> None:
        if app.bot.is_running():
            app.bot.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
