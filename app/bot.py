from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from .adb_client import AdbClient
from .image_matcher import ImageMatcher

LogFn = Callable[[str], None]


@dataclass
class BotSettings:
    threshold: float
    loop_delay_seconds: float
    action_delay_seconds: float
    scan_region: Optional[Tuple[int, int, int, int]]
    auto_reconnect: bool
    features: Dict[str, bool]
    templates: Dict[str, str]


class GameBot:
    def __init__(self, adb_client: AdbClient, matcher: ImageMatcher, logger: LogFn = print):
        self.adb = adb_client
        self.matcher = matcher
        self.logger = logger
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._settings: Optional[BotSettings] = None

    def log(self, message: str) -> None:
        self.logger(message)

    def is_running(self) -> bool:
        return self._running

    def start(self, settings: BotSettings) -> bool:
        with self._lock:
            if self._running:
                self.log("[Bot] Bot đang chạy rồi.")
                return False
            self._running = True
            self._settings = settings
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            self.log("[Bot] Đã start bot.")
            return True

    def stop(self) -> None:
        with self._lock:
            self._running = False
        self.log("[Bot] Đã gửi lệnh stop.")

    def _ensure_device(self) -> bool:
        if self.adb.device_id:
            return True
        device = self.adb.auto_connect()
        return device is not None

    def _loop(self) -> None:
        self.log("[Bot] Bot thread started")
        while self._running:
            settings = self._settings
            if settings is None:
                self.log("[Bot] Thiếu settings, bot dừng.")
                self._running = False
                break

            try:
                if not self._ensure_device():
                    raise RuntimeError("Không kết nối được LDPlayer ADB")

                screen = self.adb.screencap()
                clicked = self._run_actions(screen, settings)
                if not clicked:
                    self.log("[Bot] Không tìm thấy action nào.")
                    time.sleep(settings.loop_delay_seconds)

            except Exception as exc:
                self.log(f"[Bot] Error: {exc}")
                if settings.auto_reconnect:
                    self.adb.device_id = None
                    self.log("[Bot] Đang thử reconnect ADB...")
                    self.adb.auto_connect()
                time.sleep(max(1.0, settings.loop_delay_seconds))

        self.log("[Bot] Bot stopped")

    def _run_actions(self, screen, settings: BotSettings) -> bool:
        clicked_any = False
        for key, label in [("build", "Build"), ("collect", "Collect"), ("upgrade", "Upgrade")]:
            if not settings.features.get(key, False):
                continue
            template_path = settings.templates.get(key, "")
            if not template_path:
                continue

            try:
                match = self.matcher.find_template(
                    screen_bgr=screen,
                    template_path=template_path,
                    threshold=settings.threshold,
                    region=settings.scan_region,
                )
            except Exception as exc:
                self.log(f"[{label}] Error: {exc}")
                continue

            if not match:
                self.log(f"[{label}] Not found")
                continue

            try:
                self.adb.tap(match.x, match.y)
                self.log(f"[{label}] Clicked at ({match.x}, {match.y}) score={match.score:.3f}")
                clicked_any = True
                time.sleep(settings.action_delay_seconds)
            except Exception as exc:
                self.log(f"[{label}] Error: {exc}")

        return clicked_any
