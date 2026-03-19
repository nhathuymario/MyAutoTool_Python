from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict


def get_base_dir() -> Path:
    """
    Thư mục để đọc/ghi file người dùng như config.json, logs...
    - Chạy .py: thư mục gốc project
    - Chạy .exe: thư mục chứa file .exe
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_resource_dir() -> Path:
    """
    Thư mục chứa resource đóng gói.
    - Chạy .py: thư mục gốc project
    - Chạy .exe: thư mục tạm _MEIPASS
    """
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def resource_path(relative_path: str) -> Path:
    """
    Trả về đường dẫn resource đúng cho cả .py và .exe
    """
    return get_resource_dir() / relative_path


BASE_DIR = get_base_dir()
RESOURCE_DIR = get_resource_dir()
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ldplayer_path": r"E:\LDPlayer\LDPlayer9\dnplayer.exe",
    "adb_path": r"",
    "ldconsole_path": r"E:\LDPlayer\LDPlayer9\ldconsole.exe",
    "window_title_keywords": ["LDPlayer", "dnplayer"],
    "device_ip": "127.0.0.1",
    "candidate_ports": [5555, 5556, 5557],
    "game_package": "",
    "game_activity": "",
    "scan_region": None,
    "default_threshold": 0.75,
    "loop_delay_seconds": 1.0,
    "action_delay_seconds": 0.35,
    "selected_feature": "adventure",
    "auto_reconnect": True,
    "templates": {
        "game_icon": "assets/images/game_icon.png",
        "level": "assets/images/level.png",
        "level1": "assets/images/level1.png",
        "claim": "assets/images/claim.png",
        "cancel": "assets/images/cancel.png",
        "up": "assets/images/up.png",
        "tap": "assets/images/tap.png",
        "dots": "assets/images/dots.png",
        "dot": "assets/images/dot.png",
        "level2": "assets/images/level2.png",
        "level3": "assets/images/level3.png",
        "level4": "assets/images/level4.png",
        "level6": "assets/images/level6.png",
        "battle": "assets/images/battle.png",
        "battle1": "assets/images/battle1.png",
        "ready": "assets/images/ready.png",
        "exit": "assets/images/exit.png",
        "victory": "assets/images/victory.png",
        "victorythap": "assets/images/victorythap.png",
        "next_stage": "assets/images/next_stage.png",
        "skip": "assets/images/skip.png",
    },
    "features": {
        "build": True,
        "collect": True,
        "upgrade": True,
    },
}


def deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    result = deepcopy(base)
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return deepcopy(DEFAULT_CONFIG)

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    return deep_merge(DEFAULT_CONFIG, data)


def save_config(config: Dict[str, Any]) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def resolve_path(relative_or_absolute: str) -> Path:
    path = Path(relative_or_absolute)

    if path.is_absolute():
        return path

    candidates = [
        RESOURCE_DIR / path,
        BASE_DIR / "_internal" / path,
        BASE_DIR / path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]

def resolve_image_dir() -> Path:
    candidates = [
        RESOURCE_DIR / "assets" / "images",
        BASE_DIR / "_internal" / "assets" / "images",
        BASE_DIR / "assets" / "images",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]