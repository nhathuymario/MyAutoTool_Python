from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Callable, Iterable, List, Optional

try:
    import pygetwindow as gw
except Exception:  # pragma: no cover
    gw = None

LogFn = Callable[[str], None]


class LDPlayerController:
    def __init__(
        self,
        ldplayer_path: str,
        ldconsole_path: str,
        title_keywords: Iterable[str],
        logger: LogFn = print
    ):
        self.ldplayer_path = str(Path(ldplayer_path))
        self.ldconsole_path = str(Path(ldconsole_path))
        self.title_keywords = [kw.lower().strip() for kw in title_keywords if kw.strip()]
        self.logger = logger

        # Các title cần bỏ qua để không focus nhầm cửa sổ tool
        self.exclude_keywords = [
            "auto tool",
            "ldplayer auto tool",
            "tool",
        ]

    def log(self, message: str) -> None:
        self.logger(message)

    def open_ldplayer(self) -> bool:
        path = Path(self.ldplayer_path)
        if not path.exists():
            self.log(f"[LDPlayer] Không tìm thấy file: {path}")
            return False
        try:
            subprocess.Popen([str(path)])
            self.log("[LDPlayer] Đã gửi lệnh mở LDPlayer.")
            return True
        except Exception as exc:
            self.log(f"[LDPlayer] Lỗi mở LDPlayer: {exc}")
            return False

    def wait_boot(self, seconds: int = 15) -> None:
        for i in range(seconds):
            time.sleep(1)
            self.log(f"[LDPlayer] Đang chờ khởi động... {i + 1}/{seconds}")

    def _is_valid_ldplayer_title(self, title: str) -> bool:
        title = (title or "").strip()
        if not title:
            return False

        lowered = title.lower()

        # Bỏ qua cửa sổ tool của chính bạn
        if any(bad in lowered for bad in self.exclude_keywords):
            return False

        # Nếu có keyword cấu hình thì dùng keyword đó
        if self.title_keywords:
            return any(keyword in lowered for keyword in self.title_keywords)

        # fallback chung
        return "ldplayer" in lowered or "dnplayer" in lowered

    def focus_window(self) -> bool:
        if gw is None:
            self.log("[LDPlayer] Chưa cài pygetwindow, không focus được cửa sổ.")
            return False

        try:
            all_windows = [w for w in gw.getAllWindows() if (w.title or "").strip()]
            all_titles = [w.title for w in all_windows]
            self.log(f"[LDPlayer] Window titles tìm thấy: {all_titles}")

            candidates = [w for w in all_windows if self._is_valid_ldplayer_title(w.title)]

            if not candidates:
                self.log("[LDPlayer] Không tìm thấy cửa sổ LDPlayer hợp lệ.")
                return False

            # Ưu tiên title có chữ LDPlayer hoặc dnplayer rõ ràng hơn
            def score_window(win) -> int:
                title = (win.title or "").lower()
                score = 0
                if "ldplayer" in title:
                    score += 3
                if "dnplayer" in title:
                    score += 2
                if "main" in title:
                    score += 1
                return score

            candidates.sort(key=score_window, reverse=True)
            win = candidates[0]

            if win.isMinimized:
                win.restore()
                time.sleep(0.3)

            win.activate()
            time.sleep(0.3)

            self.log(f"[LDPlayer] Đã focus cửa sổ: {win.title}")
            return True

        except Exception as exc:
            self.log(f"[LDPlayer] Lỗi focus cửa sổ: {exc}")
            return False

    def list_instances(self) -> Optional[str]:
        path = Path(self.ldconsole_path)
        if not path.exists():
            self.log("[LDPlayer] Không có ldconsole.exe để đọc instance.")
            return None
        try:
            proc = subprocess.run(
                [str(path), "list2"],
                capture_output=True,
                text=True,
                timeout=10
            )
            text = (proc.stdout or "").strip() or (proc.stderr or "").strip()
            self.log(f"[LDPlayer] list2:\n{text or 'Không có dữ liệu'}")
            return text
        except Exception as exc:
            self.log(f"[LDPlayer] Lỗi gọi ldconsole list2: {exc}")
            return None