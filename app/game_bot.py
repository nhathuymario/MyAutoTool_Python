from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Dict, Optional

from app.adb_client import AdbClient
from app.image_matcher import find_template

LogFn = Callable[[str], None]


class GameBot:
    def __init__(self, adb: AdbClient, image_dir: str, logger: LogFn = print):
        self.adb = adb
        self.image_dir = Path(image_dir)
        self.logger = logger

        self.thresholds: Dict[str, float] = {
            "battle": 0.72,
            "ready": 0.72,
            "skip": 0.72,
            "victory": 0.72,
            "next_stage": 0.72,
            "game_icon": 0.72,
        }

        self.delays: Dict[str, float] = {
            "after_tap": 0.8,
            "loop_idle": 1.0,
            "game_load": 8.0,
        }

    def log(self, message: str) -> None:
        self.logger(message)

    def img(self, name: str) -> str:
        return str(self.image_dir / f"{name}.png")

    def capture(self):
        return self.adb.screencap()

    def template_exists(self, image_name: str) -> bool:
        path = Path(self.img(image_name))
        if not path.exists():
            self.log(f"[{image_name}] Thiếu template: {path}")
            return False
        return True

    def tap_image(
        self,
        screen,
        image_name: str,
        threshold: Optional[float] = None,
        label: Optional[str] = None,
    ) -> bool:
        threshold = threshold if threshold is not None else self.thresholds.get(image_name, 0.75)
        label = label or image_name

        if not self.template_exists(image_name):
            return False

        try:
            match = find_template(screen, self.img(image_name), threshold=threshold)
        except Exception as exc:
            self.log(f"[{label}] Lỗi match ảnh: {exc}")
            return False

        if not match:
            return False

        self.adb.tap(match.x, match.y)
        self.log(f"[{label}] Tap tại ({match.x}, {match.y}) score={match.score:.3f}")
        time.sleep(self.delays["after_tap"])
        return True

    def exists_image(
        self,
        screen,
        image_name: str,
        threshold: Optional[float] = None,
        label: Optional[str] = None,
    ) -> bool:
        threshold = threshold if threshold is not None else self.thresholds.get(image_name, 0.75)
        label = label or image_name

        if not self.template_exists(image_name):
            return False

        try:
            match = find_template(screen, self.img(image_name), threshold=threshold)
        except Exception as exc:
            self.log(f"[{label}] Lỗi kiểm tra ảnh: {exc}")
            return False

        if match:
            self.log(f"[{label}] Tìm thấy score={match.score:.3f}")
            return True

        return False

    def do_battle(self, screen) -> bool:
        return self.tap_image(screen, "battle", label="Battle")

    def do_ready(self, screen) -> bool:
        return self.tap_image(screen, "ready", label="Ready")

    def do_skip(self, screen) -> bool:
        return self.tap_image(screen, "skip", label="Skip")

    def do_next_stage(self, screen) -> bool:
        return self.tap_image(screen, "next_stage", label="NextStage")

    def do_victory(self, screen) -> bool:
        return self.tap_image(screen, "victory", label="Victory")

    def wait_until_game_ready(self, timeout: int = 20) -> bool:
        start = time.time()

        while time.time() - start < timeout:
            try:
                screen = self.capture()
            except Exception as exc:
                self.log(f"[Game] Lỗi capture: {exc}")
                time.sleep(1.0)
                continue

            if self.exists_image(screen, "battle", label="Battle"):
                self.log("[Game] Đã thấy Battle, game sẵn sàng.")
                return True

            if self.exists_image(screen, "ready", label="Ready"):
                self.log("[Game] Đã thấy Ready, game sẵn sàng.")
                return True

            if self.exists_image(screen, "next_stage", label="NextStage"):
                self.log("[Game] Đã thấy Next Stage, game sẵn sàng.")
                return True

            self.log("[Game] Đang chờ màn hình có nút thao tác...")
            time.sleep(1.0)

        self.log("[Game] Hết thời gian chờ game sẵn sàng.")
        return False

    def run_priority_once(self, features: Dict[str, bool]) -> bool:
        try:
            screen = self.capture()
        except Exception as exc:
            self.log(f"[Game] Lỗi capture: {exc}")
            return False

        if features.get("skip", True) and self.do_skip(screen):
            return True

        if features.get("next_stage", True) and self.do_next_stage(screen):
            return True

        if features.get("ready", True) and self.do_ready(screen):
            return True

        if features.get("battle", True) and self.do_battle(screen):
            return True

        if self.do_victory(screen):
            return True

        return False