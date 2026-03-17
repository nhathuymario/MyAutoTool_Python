from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, List, Tuple

from app.adb_client import AdbClient
from app.image_matcher import find_template

LogFn = Callable[[str], None]


class BaseFeature:
    key = "base"
    name = "Base Feature"

    def __init__(self, adb: AdbClient, image_dir: str, logger: LogFn = print):
        self.adb = adb
        self.image_dir = Path(image_dir)
        self.logger = logger

        self.threshold = 0.75
        self.after_click_delay = 0.35

    def log(self, msg: str):
        self.logger(msg)

    def update_settings(self, threshold: float, after_click_delay: float):
        self.threshold = threshold
        self.after_click_delay = after_click_delay

    def set_image_dir(self, image_dir: str):
        self.image_dir = Path(image_dir)

    def img(self, name: str) -> str:
        return str(self.image_dir / f"{name}.png")

    def capture(self):
        return self.adb.screencap()

    def tap_if_found(self, screen, name: str, extra_wait: float = 0.0) -> bool:
        path = self.img(name)

        if not Path(path).exists():
            self.log(f"[{self.name}] [{name}] thiếu template")
            return False

        try:
            match = find_template(screen, path, threshold=self.threshold)
        except Exception as e:
            self.log(f"[{self.name}] [{name}] match lỗi: {e}")
            return False

        if not match:
            return False

        self.adb.tap(match.x, match.y)
        self.log(
            f"[{self.name}] [{name}] click ({match.x},{match.y}) score={match.score:.3f}"
        )

        time.sleep(self.after_click_delay)

        if extra_wait > 0:
            self.log(f"[{self.name}] [{name}] đợi {extra_wait}s")
            time.sleep(extra_wait)

        return True

    def any_template_found(self, screen, names: list[str]) -> bool:
        for name in names:
            path = self.img(name)

            if not Path(path).exists():
                continue

            try:
                match = find_template(screen, path, threshold=self.threshold)
            except Exception:
                continue

            if match:
                return True

        return False

    def tap_cancel_if_safe(
        self,
        screen,
        cancel_name: str = "cancel",
        block_if_found: list[str] | None = None,
        extra_wait: float = 0.0,
    ) -> bool:
        if block_if_found is None:
            block_if_found = []

        if self.any_template_found(screen, block_if_found):
            self.log(f"[{self.name}] còn nút khác, chưa bấm [{cancel_name}]")
            return False

        return self.tap_if_found(screen, cancel_name, extra_wait=extra_wait)

    def run_actions(self, actions: List[Tuple[str, float]]) -> bool:
        try:
            screen = self.capture()
        except Exception as e:
            self.log(f"[{self.name}] capture lỗi: {e}")
            return False

        for name, wait_time in actions:
            if self.tap_if_found(screen, name, extra_wait=wait_time):
                return True

        return False

    def run_once(self) -> bool:
        raise NotImplementedError