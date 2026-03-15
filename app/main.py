from app.adb_client import AdbClient
from app.bot import LdPlayerBot
from app.config import (
    ADB_PATH,
    DEVICE_SERIAL,
    SCREEN_PATH,
    BUTTON_STEPS,
    MATCH_THRESHOLD,
    SCAN_INTERVAL,
    MAX_ACTIONS,
)


def main() -> None:
    adb = AdbClient(ADB_PATH, DEVICE_SERIAL)

    out, err, code = adb.get_screen_size()
    if code != 0:
        print("Cannot connect to LDPlayer:", err or out)
        return

    print("Connected:", out)

    bot = LdPlayerBot(
        adb=adb,
        screen_path=SCREEN_PATH,
        steps=BUTTON_STEPS,
        threshold=MATCH_THRESHOLD,
        scan_interval=SCAN_INTERVAL,
        max_actions=MAX_ACTIONS,
    )

    bot.start()


if __name__ == "__main__":
    main()