import subprocess
from typing import Tuple


class AdbClient:
    def __init__(self, adb_path: str, serial: str):
        self.adb_path = adb_path
        self.serial = serial

    def _run(self, args: list[str]) -> Tuple[str, str, int]:
        cmd = [self.adb_path, "-s", self.serial] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def shell(self, command: str) -> Tuple[str, str, int]:
        return self._run(["shell"] + command.split())

    def tap(self, x: int, y: int) -> Tuple[str, str, int]:
        return self._run(["shell", "input", "tap", str(x), str(y)])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 200) -> Tuple[str, str, int]:
        return self._run([
            "shell", "input", "swipe",
            str(x1), str(y1), str(x2), str(y2), str(duration_ms)
        ])

    def screencap_pull(self, local_path: str) -> Tuple[str, str, int]:
        remote_path = "/sdcard/__auto_screen.png"

        out1, err1, code1 = self._run(["shell", "screencap", "-p", remote_path])
        if code1 != 0:
            return out1, err1, code1

        cmd = [self.adb_path, "-s", self.serial, "pull", remote_path, local_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode

    def get_screen_size(self) -> Tuple[str, str, int]:
        return self._run(["shell", "wm", "size"])