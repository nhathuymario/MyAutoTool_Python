from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from app.adb_client import AdbClient
from app.features import FEATURES

LogFn = Callable[[str], None]


class BotManager:
    def __init__(self, adb: AdbClient, image_dir: str, logger: LogFn = print):
        self.adb = adb
        self.logger = logger
        self.image_dir = image_dir

        self.running = False
        self.thread: Optional[threading.Thread] = None

        self.current_feature_key: Optional[str] = None
        self.current_feature = None

        self.loop_delay = 1.0
        self.action_delay = 0.35
        self.threshold = 0.75

        self.game_package = "com.devsisters.ck"
        self.game_activity = "com.devsisters.plugin.OvenUnityPlayerActivity"

    def log(self, msg: str) -> None:
        self.logger(msg)

    def is_running(self) -> bool:
        return self.running

    def configure(
        self,
        image_dir: str,
        loop_delay: float,
        action_delay: float,
        threshold: float,
        game_package: str,
        game_activity: str,
    ) -> None:
        self.image_dir = image_dir
        self.loop_delay = loop_delay
        self.action_delay = action_delay
        self.threshold = threshold
        self.game_package = game_package
        self.game_activity = game_activity

        if self.current_feature:
            self.current_feature.set_image_dir(image_dir)
            self.current_feature.update_settings(
                threshold=threshold,
                after_click_delay=action_delay,
            )

    def set_feature(self, feature_key: str) -> None:
        feature_cls = FEATURES.get(feature_key)

        if not feature_cls:
            raise ValueError(f"Không tìm thấy feature: {feature_key}")

        self.current_feature_key = feature_key
        self.current_feature = feature_cls(
            adb=self.adb,
            image_dir=self.image_dir,
            logger=self.logger,
        )
        self.current_feature.update_settings(
            threshold=self.threshold,
            after_click_delay=self.action_delay,
        )

    def start(self) -> None:
        if self.running:
            self.log("[Bot] đã chạy")
            return

        if not self.current_feature:
            self.log("[Bot] chưa chọn chức năng")
            return

        device = self.adb.auto_connect()

        if not device:
            self.log("[Bot] không kết nối được adb")
            return

        self.log(f"[Bot] device: {device}")

        try:
            if self.game_package and self.game_activity:
                self.adb.start_app(self.game_package, self.game_activity)
                self.log("[Bot] mở game")
                time.sleep(6)
        except Exception as e:
            self.log(f"[Bot] lỗi mở game: {e}")

        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        self.log("[Bot] stop")

    def loop(self) -> None:
        self.log(f"[Bot] loop started - feature={self.current_feature_key}")

        while self.running:
            try:
                if self.current_feature is None:
                    self.log("[Bot] chưa có feature để chạy")
                    time.sleep(1)
                    continue

                acted = self.current_feature.run_once()

                if not acted:
                    time.sleep(self.loop_delay)

            except Exception as e:
                self.log(f"[Bot] lỗi: {e}")
                time.sleep(1)

        self.log("[Bot] loop stopped")