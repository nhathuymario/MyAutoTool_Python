from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_resource_dir() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)

    base_dir = get_base_dir()
    internal_dir = base_dir / "_internal"
    if internal_dir.exists():
        return internal_dir

    return base_dir


class AdbClient:
    def __init__(
        self,
        adb_path: Optional[str] = None,
        device_id: Optional[str] = None,
        logger=print,
    ):
        self.logger = logger
        self.device_id = device_id

        cleaned_adb_path = None
        if isinstance(adb_path, str):
            cleaned = adb_path.strip().strip('"').strip("'")
            if cleaned:
                cleaned_adb_path = cleaned

        self.adb_path = self._resolve_adb_path(cleaned_adb_path)

        self.log(f"[ADB] Đường dẫn đang dùng: {self.adb_path}")
        self.log(
            f"[ADB] Exists: "
            f"{Path(self.adb_path).exists() if self.adb_path != 'adb' else 'PATH mode'}"
        )

    def log(self, message: str) -> None:
        if self.logger:
            self.logger(message)

    def _resolve_adb_path(self, adb_path: Optional[str]) -> str:
        base_dir = get_base_dir()
        resource_dir = get_resource_dir()

        candidates: list[Path] = []

        if adb_path:
            candidates.append(Path(adb_path))

        candidates.extend([
            resource_dir / "platform_tools" / "adb.exe",
            base_dir / "platform_tools" / "adb.exe",
            resource_dir / "adb.exe",
            base_dir / "adb.exe",
        ])

        for candidate in candidates:
            try:
                candidate = candidate.expanduser().resolve()
            except Exception:
                candidate = Path(str(candidate))

            if candidate.exists() and candidate.is_file():
                return str(candidate)

        return "adb"

    def _base_cmd(self) -> list[str]:
        cmd = [self.adb_path]
        if self.device_id:
            cmd += ["-s", self.device_id]
        return cmd

    def _run_subprocess(
        self,
        cmd: list[str],
        check: bool = False,
        text: bool = True,
    ) -> subprocess.CompletedProcess:
        exe = cmd[0]

        if exe != "adb":
            exe_path = Path(exe)
            if not exe_path.exists():
                raise FileNotFoundError(f"Không tìm thấy adb.exe: {exe}")
            if not exe_path.is_file():
                raise RuntimeError(f"adb_path không phải file: {exe}")

        self.debug = False

        if self.debug:
            self.log(f"[ADB] RUN: {cmd}")

        creationflags = 0
        startupinfo = None

        if sys.platform.startswith("win"):
            creationflags = subprocess.CREATE_NO_WINDOW
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=text,
                check=False,
                creationflags=creationflags,
                startupinfo=startupinfo,
            )
        except OSError as e:
            raise RuntimeError(
                f"Không chạy được lệnh ADB.\n"
                f"Command: {cmd}\n"
                f"adb_path={exe!r}\n"
                f"Lỗi gốc: {e}"
            ) from e

        if check and result.returncode != 0:
            raise RuntimeError(
                f"ADB command failed: {' '.join(cmd)}\n"
                f"stdout={result.stdout}\n"
                f"stderr={result.stderr}"
            )

        return result

    def run(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess:
        cmd = self._base_cmd() + args
        return self._run_subprocess(cmd, check=check, text=True)

    def shell(self, command: str, check: bool = False) -> subprocess.CompletedProcess:
        return self.run(["shell", command], check=check)

    def shell_args(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess:
        return self.run(["shell"] + args, check=check)

    def connect(self, host: str, port: int) -> subprocess.CompletedProcess:
        return self._run_subprocess(
            [self.adb_path, "connect", f"{host}:{port}"],
            check=False,
            text=True,
        )

    def disconnect(self, host: str, port: int) -> subprocess.CompletedProcess:
        return self._run_subprocess(
            [self.adb_path, "disconnect", f"{host}:{port}"],
            check=False,
            text=True,
        )

    def get_devices(self) -> List[str]:
        result = self._run_subprocess(
            [self.adb_path, "devices"],
            check=False,
            text=True,
        )

        devices: List[str] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if "\tdevice" in line:
                devices.append(line.split("\t")[0])
        return devices

    def auto_connect(
        self,
        device_ip: str = "127.0.0.1",
        candidate_ports: Optional[List[int]] = None,
    ) -> Optional[str]:
        if candidate_ports is None:
            candidate_ports = [5555, 5556, 5557, 5558, 5559, 5565, 5575]

        devices = self.get_devices()
        self.log(f"[ADB] Devices hiện có trước khi connect: {devices}")

        if devices:
            preferred = "Đã kết nối LD"
            if preferred in devices:
                self.device_id = preferred
            else:
                self.device_id = devices[0]

            self.log(f"[ADB] Đã dùng device đang có: {self.device_id}")
            return self.device_id

        for port in candidate_ports:
            target = f"{device_ip}:{port}"
            self.log(f"[ADB] Thử kết nối {target} ...")

            result = self.connect(device_ip, port)
            output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()

            if output:
                self.log(f"[ADB] Kết quả {target}: {output}")

            devices = self.get_devices()
            if target in devices:
                self.device_id = target
                self.log(f"[ADB] Kết nối thành công: {self.device_id}")
                return self.device_id

            if devices:
                preferred = "emulator-5554"
                if preferred in devices:
                    self.device_id = preferred
                    self.log(f"[ADB] Dùng device sau khi connect: {self.device_id}")
                    return self.device_id

        self.log("[ADB] Không kết nối được tới device nào.")
        return None

    def start_app(self, package: str, activity: str) -> subprocess.CompletedProcess:
        if not package or not activity:
            raise ValueError("Thiếu package hoặc activity")

        return self.shell_args(
            ["am", "start", "-n", f"{package}/{activity}"],
            check=False,
        )

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
        result = self._run_subprocess(cmd, check=False, text=False)

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