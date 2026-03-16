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
    def __init__(self, ldplayer_path: str, ldconsole_path: str, title_keywords: Iterable[str], logger: LogFn = print):
        self.ldplayer_path = str(Path(ldplayer_path))
        self.ldconsole_path = str(Path(ldconsole_path))
        self.title_keywords = [kw.lower() for kw in title_keywords]
        self.logger = logger

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

    def focus_window(self) -> bool:
        if gw is None:
            self.log("[LDPlayer] Chưa cài pygetwindow, không focus được cửa sổ.")
            return False
        try:
            titles = gw.getAllTitles()
            matches: List[str] = []
            for title in titles:
                lowered = title.lower()
                if any(keyword in lowered for keyword in self.title_keywords):
                    matches.append(title)
            if not matches:
                self.log("[LDPlayer] Không tìm thấy cửa sổ LDPlayer.")
                return False
            win = gw.getWindowsWithTitle(matches[0])[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            self.log(f"[LDPlayer] Đã focus cửa sổ: {matches[0]}")
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
            proc = subprocess.run([str(path), "list2"], capture_output=True, text=True, timeout=10)
            text = (proc.stdout or "").strip() or (proc.stderr or "").strip()
            self.log(f"[LDPlayer] list2:\n{text or 'Không có dữ liệu'}")
            return text
        except Exception as exc:
            self.log(f"[LDPlayer] Lỗi gọi ldconsole list2: {exc}")
            return None
