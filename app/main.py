from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Optional, Tuple

from .adb_client import AdbClient
from .bot import BotManager
from .config_manager import BASE_DIR, load_config, save_config
from .image_matcher import ImageMatcher
from .ldplayer import LDPlayerController
from .ui import AppLogger, AutoToolUI


class AutoToolApp:

    def __init__(self, root: tk.Tk):

        self.root = root
        self.root.title("LDPlayer Auto Tool")
        self.root.geometry("1100x700")
        self.root.minsize(980, 620)

        self.config = load_config()

        default_adb_path = self.config.get(
            "adb_path", r"E:\LDPlayer\LDPlayer9\adb.exe"
        )

        default_image_dir = self.config.get(
            "image_dir",
            str(BASE_DIR / "assets" / "images")
        )

        self.var_ldplayer_path = tk.StringVar(
            value=self.config.get("ldplayer_path", "")
        )

        self.var_adb_path = tk.StringVar(value=default_adb_path)

        self.var_ldconsole_path = tk.StringVar(
            value=self.config.get("ldconsole_path", "")
        )

        self.var_image_dir = tk.StringVar(value=default_image_dir)

        self.var_game_package = tk.StringVar(
            value=self.config.get("game_package", "com.devsisters.ck")
        )

        self.var_game_activity = tk.StringVar(
            value=self.config.get(
                "game_activity",
                "com.devsisters.plugin.OvenUnityPlayerActivity"
            )
        )

        self.var_threshold = tk.DoubleVar(
            value=float(self.config.get("default_threshold", 0.75))
        )

        self.var_loop_delay = tk.DoubleVar(
            value=float(self.config.get("loop_delay_seconds", 1.0))
        )

        self.var_action_delay = tk.DoubleVar(
            value=float(self.config.get("action_delay_seconds", 0.35))
        )

        self.var_scan_region = tk.StringVar(
            value=self.region_to_string(self.config.get("scan_region"))
        )

        self.var_device_id = tk.StringVar(value="Chưa kết nối")

        self.log_box = AutoToolUI(self).build()

        self.logger = AppLogger(self.log_box)

        self.matcher = ImageMatcher()

        self.adb = AdbClient(
            adb_path=self.var_adb_path.get().strip(),
            logger=self.logger,
        )

        self.ldplayer = LDPlayerController(
            ldplayer_path=self.var_ldplayer_path.get().strip(),
            ldconsole_path=self.var_ldconsole_path.get().strip(),
            title_keywords=self.config.get(
                "window_title_keywords",
                ["LDPlayer", "dnplayer"]
            ),
            logger=self.logger,
        )

        self.bot = BotManager(
            adb=self.adb,
            image_dir=self.var_image_dir.get().strip(),
            logger=self.logger,
        )

        self.logger("Tool đã sẵn sàng.")
        self.logger(f"Project: {BASE_DIR}")

    @staticmethod
    def region_to_string(region):

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
            raise ValueError("Region phải dạng left,top,width,height")

        values = tuple(int(p) for p in parts)

        if values[2] <= 0 or values[3] <= 0:
            raise ValueError("width height phải > 0")

        return values

    def sync_runtime_paths(self):

        self.ldplayer.ldplayer_path = self.var_ldplayer_path.get().strip()

        self.ldplayer.ldconsole_path = self.var_ldconsole_path.get().strip()

        self.adb.adb_path = self.var_adb_path.get().strip()

        self.bot.game.image_dir = Path(self.var_image_dir.get().strip())

    def handle_open_ldplayer(self):

        self.sync_runtime_paths()

        ok = self.ldplayer.open_ldplayer()

        if ok:
            self.ldplayer.wait_boot(10)

    def handle_focus_ldplayer(self):

        self.ldplayer.focus_window()

    def handle_list_instances(self):

        self.sync_runtime_paths()

        self.ldplayer.list_instances()

    def handle_connect_adb(self):

        self.sync_runtime_paths()

        device = self.adb.auto_connect()

        self.var_device_id.set(device or "Chưa kết nối")

    def ensure_connected(self):

        if self.adb.device_id:
            self.var_device_id.set(self.adb.device_id)
            return True

        self.handle_connect_adb()

        return bool(self.adb.device_id)

    def handle_open_game_by_package(self):

        if not self.ensure_connected():
            return

        self.sync_runtime_paths()

        package = self.var_game_package.get().strip()

        activity = self.var_game_activity.get().strip()

        try:

            result = self.adb.start_app(package, activity)

            self.logger(f"[Game] start_app rc={result.returncode}")

            if result.returncode == 0:
                self.logger("[Game] Game started")

        except Exception as e:

            self.logger(f"[Game] lỗi mở game: {e}")

    def handle_open_game_by_icon(self):

        if not self.ensure_connected():
            return

        screen = self.adb.screencap()

        template = self.config.get("templates", {}).get("game_icon")

        if not template:
            self.logger("Thiếu template game_icon")
            return

        match = self.matcher.find_template(
            screen_bgr=screen,
            template_path=template,
            threshold=self.var_threshold.get()
        )

        if not match:
            self.logger("Không tìm thấy icon game")
            return

        self.adb.tap(match.x, match.y)

        self.logger(f"Click icon game {match.x},{match.y}")

    def handle_save_screenshot(self):

        if not self.ensure_connected():
            return

        try:

            path = BASE_DIR / "debug" / "manual_capture.png"

            path.parent.mkdir(exist_ok=True)

            result = self.adb.save_screenshot(str(path))

            self.logger(f"Saved screenshot: {result}")

        except Exception as e:

            self.logger(f"Lỗi screenshot: {e}")

    def handle_test_template(self, key: str, label: str):

        if not self.ensure_connected():
            return

        template = self.config.get("templates", {}).get(key)

        if not template:
            self.logger(f"Thiếu template {key}")
            return

        screen = self.adb.screencap()

        match = self.matcher.find_template(
            screen_bgr=screen,
            template_path=template,
            threshold=self.var_threshold.get()
        )

        if not match:

            self.logger(f"{label} not found")

            return

        self.logger(
            f"{label} found {match.x},{match.y} score={match.score:.3f}"
        )

    def handle_start_bot(self):

        if not self.ensure_connected():
            return

        try:

            self.sync_runtime_paths()

            self.logger("[Bot] starting")

            self.bot.start()

        except Exception as e:

            self.logger(f"[Bot] lỗi start: {e}")

    def handle_stop_bot(self):

        self.bot.stop()

    def safe_region(self):

        return self.parse_region(self.var_scan_region.get())

    def handle_save_config(self):

        try:

            region = self.safe_region()

            self.config["ldplayer_path"] = self.var_ldplayer_path.get().strip()

            self.config["adb_path"] = self.var_adb_path.get().strip()

            self.config["ldconsole_path"] = self.var_ldconsole_path.get().strip()

            self.config["image_dir"] = self.var_image_dir.get().strip()

            self.config["game_package"] = self.var_game_package.get().strip()

            self.config["game_activity"] = self.var_game_activity.get().strip()

            self.config["default_threshold"] = self.var_threshold.get()

            self.config["loop_delay_seconds"] = self.var_loop_delay.get()

            self.config["action_delay_seconds"] = self.var_action_delay.get()

            self.config["scan_region"] = list(region) if region else None

            save_config(self.config)

            self.logger("Config saved")

        except Exception as e:

            messagebox.showerror("Config error", str(e))


def run_app():

    root = tk.Tk()

    app = AutoToolApp(root)

    def on_close():

        if app.bot.is_running():
            app.bot.stop()

        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()