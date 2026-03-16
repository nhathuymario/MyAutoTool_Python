from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from app.adb_client import AdbClient
from app.image_matcher import find_template

LogFn = Callable[[str], None]


class GameBot:

    def __init__(self, adb: AdbClient, image_dir: str, logger: LogFn = print):
        self.adb = adb
        self.image_dir = Path(image_dir)
        self.logger = logger

        self.threshold = 0.72
        self.after_click_delay = 0.8

    def log(self, msg: str):
        self.logger(msg)

    def img(self, name: str):
        return str(self.image_dir / f"{name}.png")

    def capture(self):
        return self.adb.screencap()

    def tap_if_found(self, screen, name: str) -> bool:

        path = self.img(name)

        if not Path(path).exists():
            self.log(f"[{name}] thiếu template")
            return False

        try:
            match = find_template(screen, path, threshold=self.threshold)
        except Exception as e:
            self.log(f"[{name}] match lỗi: {e}")
            return False

        if not match:
            return False

        self.adb.tap(match.x, match.y)

        self.log(f"[{name}] click ({match.x},{match.y}) score={match.score:.3f}")

        time.sleep(self.after_click_delay)

        return True

    def run_once(self) -> bool:

        try:
            screen = self.capture()
        except Exception as e:
            self.log(f"[capture] lỗi: {e}")
            return False

        if self.tap_if_found(screen, "skip"):
            return True

        if self.tap_if_found(screen, "next_stage"):
            return True

        if self.tap_if_found(screen, "ready"):
            return True

        if self.tap_if_found(screen, "battle"):
            return True

        if self.tap_if_found(screen, "victory"):
            return True

        return False