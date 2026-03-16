from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from app.adb_client import AdbClient
from app.game_bot import GameBot

LogFn = Callable[[str], None]


class BotManager:

    def __init__(self, adb: AdbClient, image_dir: str, logger: LogFn = print):

        self.adb = adb
        self.logger = logger
        self.game = GameBot(adb, image_dir, logger)

        self.running = False
        self.thread: Optional[threading.Thread] = None

    def log(self, msg: str):
        self.logger(msg)

    def is_running(self):
        return self.running

    def start(self):

        if self.running:
            self.log("[Bot] đã chạy")
            return

        device = self.adb.auto_connect()

        if not device:
            self.log("[Bot] không kết nối được adb")
            return

        self.log(f"[Bot] device: {device}")

        try:

            self.adb.start_app(
                "com.devsisters.ck",
                "com.devsisters.plugin.OvenUnityPlayerActivity"
            )

            self.log("[Bot] mở game")

            time.sleep(6)

        except Exception as e:
            self.log(f"[Bot] lỗi mở game: {e}")

        self.running = True

        self.thread = threading.Thread(
            target=self.loop,
            daemon=True
        )

        self.thread.start()

    def stop(self):

        self.running = False
        self.log("[Bot] stop")

    def loop(self):

        self.log("[Bot] loop started")

        while self.running:

            try:

                acted = self.game.run_once()

                if not acted:
                    time.sleep(0.5)

            except Exception as e:

                self.log(f"[Bot] lỗi: {e}")

                time.sleep(1)

        self.log("[Bot] loop stopped")