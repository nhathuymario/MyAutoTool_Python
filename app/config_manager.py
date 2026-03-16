from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ldplayer_path": r"C:\LDPlayer\LDPlayer9\dnplayer.exe",
    "adb_path": r"C:\LDPlayer\LDPlayer9\adb.exe",
    "ldconsole_path": r"C:\LDPlayer\LDPlayer9\ldconsole.exe",
    "window_title_keywords": ["LDPlayer", "dnplayer"],
    "device_ip": "127.0.0.1",
    "candidate_ports": [5555, 5556, 5557],
    "game_package": "",
    "game_activity": "",
    "scan_region": None,
    "default_threshold": 0.75,
    "loop_delay_seconds": 1.0,
    "action_delay_seconds": 0.35,
    "auto_reconnect": True,
    "templates": {
    "game_icon": "assets/images/game_icon.png",

    "battle": "assets/images/battle.png",
    "battle1": "assets/images/battle1.png",
    "ready": "assets/images/ready.png",
    "victory": "assets/images/victory.png",
    "next_stage": "assets/images/next_stage.png",
    "skip": "assets/images/skip.png"
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
    return BASE_DIR / path
