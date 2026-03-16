from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

import cv2
import numpy as np

LogFn = Callable[[str], None]


@dataclass
class AdbResult:
    returncode: int
    stdout: str
    stderr: str


class AdbClient:
    def __init__(
        self,
        adb_path: str,
        device_ip: str,
        candidate_ports: Iterable[int],
        logger: LogFn = print
    ):
        self.adb_path = str(Path(adb_path))
        self.device_ip = device_ip
        self.candidate_ports = list(candidate_ports)
        self.logger = logger
        self.device_id: Optional[str] = None

    def log(self, message: str) -> None:
        self.logger(message)

    def _run(self, args: Sequence[str], timeout: int = 20, binary: bool = False) -> subprocess.CompletedProcess:
        cmd = [self.adb_path, *args]
        return subprocess.run(
            cmd,
            capture_output=True,
            text=not binary,
            timeout=timeout,
        )

    def run_text(self, args: Sequence[str], timeout: int = 20) -> AdbResult:
        proc = self._run(args, timeout=timeout, binary=False)
        return AdbResult(
            returncode=proc.returncode,
            stdout=(proc.stdout or "").strip(),
            stderr=(proc.stderr or "").strip(),
        )

    def ensure_adb_exists(self) -> bool:
        exists = Path(self.adb_path).exists()
        if not exists:
            self.log(f"[ADB] Không tìm thấy adb.exe: {self.adb_path}")
        return exists

    def list_devices(self) -> List[str]:
        result = self.run_text(["devices"])
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "adb devices failed")

        devices: List[str] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices attached"):
                continue

            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])

        return devices

    def connect(self, host: str, port: int) -> Tuple[bool, str]:
        target = f"{host}:{port}"
        result = self.run_text(["connect", target])
        text = "\n".join(p for p in [result.stdout, result.stderr] if p).strip()

        lowered = text.lower()
        ok = result.returncode == 0 and (
            "connected" in lowered
            or "already connected" in lowered
            or "already connected to" in lowered
            or not text
        )
        return ok, text

    def _device_priority(self, device: str) -> int:
        """
        Điểm càng cao càng ưu tiên.
        Ưu tiên localhost / 127.0.0.1 trước.
        """
        d = device.lower().strip()

        if d.startswith("127.0.0.1:"):
            return 100
        if d.startswith("localhost:"):
            return 95
        if d.startswith("emulator-"):
            return 80
        return 0

    def pick_best_device(self, devices: List[str]) -> Optional[str]:
        if not devices:
            return None

        ranked = sorted(devices, key=self._device_priority, reverse=True)
        best = ranked[0]

        if self._device_priority(best) <= 0:
            return None

        return best

    def auto_connect(self) -> Optional[str]:
        if not self.ensure_adb_exists():
            return None

        try:
            devices = self.list_devices()
            self.log(f"[ADB] Devices hiện có: {devices}")
        except Exception as exc:
            self.log(f"[ADB] Lỗi đọc devices: {exc}")
            devices = []

        # Ưu tiên dùng device có sẵn
        best = self.pick_best_device(devices)
        if best:
            self.device_id = best
            self.log(f"[ADB] Đã dùng device đang có: {best}")
            return best

        self.log("[ADB] Chưa thấy LDPlayer device. Bắt đầu dò port...")

        for port in self.candidate_ports:
            ok, message = self.connect(self.device_ip, int(port))
            if message:
                self.log(f"[ADB] connect {self.device_ip}:{port} -> {message}")
            time.sleep(0.25)

            # Không break ngay, cứ dò hết để adb register đủ
            # tránh trường hợp port đầu connect được nhưng device list chưa ổn định

        try:
            devices = self.list_devices()
            self.log(f"[ADB] Devices sau khi dò: {devices}")
        except Exception as exc:
            self.log(f"[ADB] Lỗi sau khi connect: {exc}")
            return None

        best = self.pick_best_device(devices)
        if best:
            self.device_id = best
            self.log(f"[ADB] Kết nối thành công: {best}")
            return best

        self.log("[ADB] Không tìm thấy LDPlayer device hoạt động.")
        return None

    def require_device(self) -> str:
        if not self.device_id:
            raise RuntimeError("Chưa có device ADB. Hãy connect trước.")
        return self.device_id

    def shell(self, *args: str, timeout: int = 20) -> AdbResult:
        device = self.require_device()
        return self.run_text(["-s", device, "shell", *args], timeout=timeout)

    def screencap(self) -> np.ndarray:
        device = self.require_device()
        proc = self._run(["-s", device, "exec-out", "screencap", "-p"], timeout=20, binary=True)

        stdout_data = proc.stdout
        stderr_data = proc.stderr

        if proc.returncode != 0 or not stdout_data:
            err = stderr_data.decode(errors="ignore") if isinstance(stderr_data, bytes) else str(stderr_data or "")
            raise RuntimeError(f"Capture failed: {err.strip() or 'no output'}")

        raw = stdout_data
        if isinstance(raw, str):
            raw = raw.encode()

        img = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError("Không decode được ảnh từ adb screencap")
        return img

    def tap(self, x: int, y: int) -> None:
        result = self.shell("input", "tap", str(int(x)), str(int(y)))
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "adb tap failed")

    def start_app(self, package_name: str, activity: str = "") -> None:
        package_name = package_name.strip()
        activity = activity.strip()

        if not package_name:
            raise RuntimeError("game_package đang trống")

        if activity:
            component = f"{package_name}/{activity}"
            result = self.shell("am", "start", "-n", component, timeout=25)
        else:
            result = self.shell(
                "monkey",
                "-p",
                package_name,
                "-c",
                "android.intent.category.LAUNCHER",
                "1",
                timeout=25
            )

        text = " ".join(p for p in [result.stdout, result.stderr] if p).strip()
        if result.returncode != 0:
            raise RuntimeError(text or "Không mở được game bằng ADB")

        self.log(f"[ADB] Launch game: {text or 'OK'}")