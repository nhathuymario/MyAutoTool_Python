import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADB_PATH = r"E:\android\platform-tools\adb.exe"
DEVICE_SERIAL = "127.0.0.1:5555"

TEMP_DIR = os.path.join(BASE_DIR, "temp")
SCREEN_PATH = os.path.join(TEMP_DIR, "screen.png")

IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images")

MATCH_THRESHOLD = 0.85
SCAN_INTERVAL = 1.0
MAX_ACTIONS = 100

BUTTON_STEPS = [
    {
        "name": "Build",
        "image": os.path.join(IMAGE_DIR, "build.png"),
        "enabled": True,
    },
    {
        "name": "Collect",
        "image": os.path.join(IMAGE_DIR, "collect.png"),
        "enabled": True,
    },
    {
        "name": "Upgrade",
        "image": os.path.join(IMAGE_DIR, "upgrade.png"),
        "enabled": True,
    },
]