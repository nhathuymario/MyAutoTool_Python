import os
from app.adb_client import AdbClient


def ensure_temp_dir(path: str) -> None:
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)


def capture_screen(adb: AdbClient, output_path: str) -> str:
    ensure_temp_dir(output_path)
    out, err, code = adb.screencap_pull(output_path)
    if code != 0:
        raise RuntimeError(f"Capture failed: {err or out}")
    return output_path