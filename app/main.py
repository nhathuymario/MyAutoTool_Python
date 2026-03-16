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
        self.log_box: Optional[tk.Text] = None
        self.logger: Optional[AppLogger] = None

        default_adb_path = self.config.get("adb_path", r"E:\LDPlayer\LDPlayer9\adb.exe")
        default_image_dir = self.config.get("image_dir", str(BASE_DIR / "assets" / "images"))

        self.var_ldplayer_path = tk.StringVar(value=self.config.get("ldplayer_path", ""))
        self.var_adb_path = tk.StringVar(value=default_adb_path)
        self.var_ldconsole_path = tk.StringVar(value=self.config.get("ldconsole_path", ""))
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

        self.var_feature_battle = tk.BooleanVar(
            value=bool(self.config.get("features", {}).get("battle", True))
        )
        self.var_feature_ready = tk.BooleanVar(
            value=bool(self.config.get("features", {}).get("ready", True))
        )
        self.var_feature_skip = tk.BooleanVar(
            value=bool(self.config.get("features", {}).get("skip", True))
        )
        self.var_feature_next_stage = tk.BooleanVar(
            value=bool(self.config.get("features", {}).get("next_stage", True))
        )

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
            title_keywords=self.config.get("window_title_keywords", ["LDPlayer", "dnplayer"]),
            logger=self.logger,
        )

        self.bot = BotManager(
            adb=self.adb,
            image_dir=self.var_image_dir.get().strip(),
            logger=self.logger,
        )

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

    def sync_runtime_paths(self) -> None:
        self.ldplayer.ldplayer_path = self.var_ldplayer_path.get().strip()
        self.ldplayer.ldconsole_path = self.var_ldconsole_path.get().strip()
        self.adb.adb_path = self.var_adb_path.get().strip()
        self.bot.game.image_dir = Path(self.var_image_dir.get().strip())

    def handle_open_ldplayer(self) -> None:
        self.sync_runtime_paths()
        ok = self.ldplayer.open_ldplayer()
        if ok:
            self.ldplayer.wait_boot(10)

    def handle_focus_ldplayer(self) -> None:
        self.ldplayer.focus_window()

    def handle_list_instances(self) -> None:
        self.sync_runtime_paths()
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

        self.sync_runtime_paths()

        package_name = self.var_game_package.get().strip()
        activity = self.var_game_activity.get().strip()

        try:
            result = self.adb.start_app(package_name, activity)
            self.logger(f"[Game] start_app rc={result.returncode}")
            if result.stdout:
                self.logger(f"[Game] stdout: {result.stdout.strip()}")
            if result.stderr:
                self.logger(f"[Game] stderr: {result.stderr.strip()}")

            if result.returncode == 0:
                self.logger(f"[Game] Đã gửi lệnh mở game: {package_name}")
            else:
                self.logger("[Game] Lệnh mở game trả về mã lỗi.")
        except Exception as exc:
            self.logger(f"[Game] Lỗi mở game bằng package: {exc}")

    def handle_open_game_by_icon(self) -> None:
        if not self.ensure_connected():
            return

        self.sync_runtime_paths()

        try:
            screen = self.adb.screencap()
            template_path = self.config.get("templates", {}).get("game_icon")

            if not template_path:
                self.logger("[Game] Chưa cấu hình templates.game_icon trong config.")
                return

            match = self.matcher.find_template(
                screen_bgr=screen,
                template_path=template_path,
                threshold=float(self.var_threshold.get()),
            )

            if not match:
                self.logger("[Game] Không tìm thấy game_icon.png")
                return

            self.adb.tap(match.x, match.y)
            self.logger(f"[Game] Đã click icon game tại ({match.x}, {match.y}) score={match.score:.3f}")

        except Exception as exc:
            self.logger(f"[Game] Lỗi mở game bằng icon: {exc}")

    def handle_save_screenshot(self) -> None:
        if not self.ensure_connected():
            return

        self.sync_runtime_paths()

        try:
            output_path = str(BASE_DIR / "debug" / "manual_capture.png")
            path = self.adb.save_screenshot(output_path)
            self.logger(f"[Debug] Đã lưu screenshot: {path}")
        except Exception as exc:
            self.logger(f"[Debug] Lỗi screenshot: {exc}")

    def handle_test_template(self, key: str, label: str) -> None:
        if not self.ensure_connected():
            return

        self.sync_runtime_paths()

        try:
            template_path = self.config.get("templates", {}).get(key)
            if not template_path:
                self.logger(f"[{label}] Chưa cấu hình templates.{key}")
                return

            screen = self.adb.screencap()
            match = self.matcher.find_template(
                screen_bgr=screen,
                template_path=template_path,
                threshold=float(self.var_threshold.get()),
            )

            if not match:
                self.logger(f"[{label}] Not found")
                output_path = str(BASE_DIR / "debug" / f"{key}_notfound.png")
                self.matcher.save_debug_image(screen, output_path)
                self.logger(f"[{label}] Saved screen: {output_path}")
                return

            self.logger(f"[{label}] Found at ({match.x}, {match.y}) score={match.score:.3f}")

        except Exception as exc:
            self.logger(f"[{label}] Error: {exc}")

    def handle_start_bot(self) -> None:
        if not self.ensure_connected():
            return

        try:
            self.sync_runtime_paths()

            self.bot.set_features({
                "battle": self.var_feature_battle.get(),
                "ready": self.var_feature_ready.get(),
                "skip": self.var_feature_skip.get(),
                "next_stage": self.var_feature_next_stage.get(),
            })

            self.config["game_package"] = self.var_game_package.get().strip()
            self.config["game_activity"] = self.var_game_activity.get().strip()

            self.logger("[Bot] Đang start bot...")
            self.bot.start()

            if self.bot.is_running():
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
            self.config["ldconsole_path"] = self.var_ldconsole_path.get().strip()
            self.config["image_dir"] = self.var_image_dir.get().strip()
            self.config["game_package"] = self.var_game_package.get().strip()
            self.config["game_activity"] = self.var_game_activity.get().strip()
            self.config["default_threshold"] = float(self.var_threshold.get())
            self.config["loop_delay_seconds"] = float(self.var_loop_delay.get())
            self.config["action_delay_seconds"] = float(self.var_action_delay.get())
            self.config["scan_region"] = list(region) if region else None
            self.config["features"] = {
                "battle": self.var_feature_battle.get(),
                "ready": self.var_feature_ready.get(),
                "skip": self.var_feature_skip.get(),
                "next_stage": self.var_feature_next_stage.get(),
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