from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Optional

from app.adb_client import AdbClient
from app.game_bot import GameBot

LogFn = Callable[[str], None]


class BotManager:
    def __init__(self, adb: AdbClient, image_dir: str, logger: LogFn = print):
        self.adb = adb
        self.logger = logger
        self.game = GameBot(adb=adb, image_dir=image_dir, logger=logger)

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.features: Dict[str, bool] = {
            "battle": True,
            "ready": True,
            "skip": True,
            "next_stage": True,
        }

    def log(self, message: str) -> None:
        self.logger(message)

    def is_running(self) -> bool:
        return self._running

    def set_features(self, features: Dict[str, bool]) -> None:
        self.features.update(features)
        self.log(f"[Bot] Features: {self.features}")

    def start(self) -> None:
        if self._running:
            self.log("[Bot] Đang chạy rồi.")
            return

        device = self.adb.auto_connect()
        if not device:
            self.log("[Bot] Không kết nối được ADB device.")
            return

        self.log(f"[Bot] Device: {device}")

        try:
            result = self.adb.start_app(
                "com.devsisters.ck",
                "com.devsisters.plugin.OvenUnityPlayerActivity"
            )

            self.log(f"[Bot] start_app rc={result.returncode}")
            if result.stdout:
                self.log(f"[Bot] stdout: {result.stdout.strip()}")
            if result.stderr:
                self.log(f"[Bot] stderr: {result.stderr.strip()}")

            self.log("[Bot] Đã gửi lệnh mở game.")
            time.sleep(8)
        except Exception as exc:
            self.log(f"[Bot] Không mở được game: {exc}")
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.log("[Bot] Đã start.")

    def stop(self) -> None:
        self._running = False
        self.log("[Bot] Đã gửi lệnh stop.")

    def _loop(self) -> None:
        self.log("[Bot] Bot loop started.")

        try:
            ok = self.game.wait_until_game_ready(timeout=20)
            if not ok:
                self.log("[Bot] Không thấy nút thao tác, vẫn tiếp tục chạy thử.")

            while self._running:
                try:
                    acted = self.game.run_priority_once(self.features)
                    if not acted:
                        self.log("[Bot] Không thấy ảnh nào để click.")
                        time.sleep(1.0)
                except Exception as exc:
                    self.log(f"[Bot] Error: {exc}")

                    device = self.adb.auto_connect()
                    if device:
                        self.log(f"[Bot] Reconnected: {device}")
                    time.sleep(1.5)

        finally:
            self._running = False
            self.log("[Bot] Bot loop stopped.")