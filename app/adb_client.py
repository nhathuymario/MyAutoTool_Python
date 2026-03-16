from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


class AdbClient:
    def __init__(
        self,
        adb_path: str = r"E:\LDPlayer\LDPlayer9\adb.exe",
        device_id: Optional[str] = None,
        logger=print,
    ):
        self.adb_path = adb_path
        self.device_id = device_id
        self.logger = logger

    def log(self, message: str) -> None:
        if self.logger:
            self.logger(message)

    def _base_cmd(self) -> list[str]:
        cmd = [self.adb_path]
        if self.device_id:
            cmd += ["-s", self.device_id]
        return cmd

    def run(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess:
        cmd = self._base_cmd() + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise RuntimeError(
                f"ADB command failed: {' '.join(cmd)}\n"
                f"stdout={result.stdout}\n"
                f"stderr={result.stderr}"
            )
        return result

    def shell(self, command: str, check: bool = False) -> subprocess.CompletedProcess:
        return self.run(["shell", command], check=check)

    def shell_args(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess:
        return self.run(["shell"] + args, check=check)

    def get_devices(self) -> List[str]:
        result = subprocess.run(
            [self.adb_path, "devices"],
            capture_output=True,
            text=True,
            check=False,
        )

        devices: List[str] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if "\tdevice" in line:
                devices.append(line.split("\t")[0])
        return devices

    def auto_connect(self) -> Optional[str]:
        devices = self.get_devices()
        self.log(f"[ADB] Devices hiện có: {devices}")

        if not devices:
            self.log("[ADB] Không tìm thấy device nào.")
            return None

        preferred = "emulator-5554"
        if preferred in devices:
            self.device_id = preferred
        else:
            self.device_id = devices[0]

        self.log(f"[ADB] Đã dùng device đang có: {self.device_id}")
        return self.device_id

    def start_app(self, package: str, activity: str) -> subprocess.CompletedProcess:
        if not package or not activity:
            raise ValueError("Thiếu package hoặc activity")

        result = self.shell_args(
            ["am", "start", "-n", f"{package}/{activity}"],
            check=False,
        )

        return result

    def tap(self, x: int, y: int) -> subprocess.CompletedProcess:
        return self.shell_args(["input", "tap", str(x), str(y)], check=False)

    def swipe(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration_ms: int = 300,
    ) -> subprocess.CompletedProcess:
        return self.shell_args(
            ["input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)],
            check=False,
        )

    def screencap(self) -> np.ndarray:
        cmd = self._base_cmd() + ["exec-out", "screencap", "-p"]
        result = subprocess.run(cmd, capture_output=True, check=False)

        if result.returncode != 0 or not result.stdout:
            raise RuntimeError(f"Lỗi chụp màn hình: {result.stderr!r}")

        data = np.frombuffer(result.stdout, dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)

        if image is None:
            raise RuntimeError("Không decode được ảnh screenshot từ ADB.")

        return image

    def save_screenshot(self, output_path: str) -> str:
        image = self.screencap()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), image)
        return str(path)