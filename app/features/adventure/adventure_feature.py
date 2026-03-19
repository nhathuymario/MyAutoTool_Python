from __future__ import annotations
import time
import pyautogui
from app.features.base_feature import BaseFeature

class AdventureFeature(BaseFeature):
    key = "adventure"
    name = "Vượt ải"

    def __init__(self, adb, image_dir, logger=print):
        super().__init__(adb, image_dir, logger)
        self.last_zoom_time = 0

        # Tọa độ giữa cửa sổ giả lập, chỉnh lại theo máy bạn
        self.zoom_x = 960
        self.zoom_y = 540

    def zoom_out(self):
        """Giữ Ctrl và lăn chuột để thu nhỏ bản đồ"""
        self.log("[Action] Đang zoom out bằng Ctrl + scroll...")

        # Đưa chuột vào vùng game
        pyautogui.moveTo(self.zoom_x, self.zoom_y, duration=0.2)
        time.sleep(0.2)

        # Giữ Ctrl và lăn chuột xuống
        pyautogui.keyDown("ctrl")
        try:
            for _ in range(8):   # chỉnh số lần scroll nếu cần
                pyautogui.scroll(-300)
                time.sleep(0.05)
        finally:
            pyautogui.keyUp("ctrl")

        time.sleep(1)

    def run_once(self) -> bool:
        current_time = time.time()
        if current_time - self.last_zoom_time > 30:
            self.zoom_out()
            self.last_zoom_time = current_time
            return True

        screen = self.capture()

        priority = [
            ("next_stage", 3),
            ("exit", 2),
            ("claim", 2),
            ("skip", 1),
            ("battle", 2),
            ("battle1", 2),
            ("ready", 2),
            ("victory", 2),
            ("tap", 1),
            ("up", 1),
            ("level6", 0),
            ("level4", 0),
            ("level3", 0),
            ("level2", 0),
            ("level1", 0),
            ("level", 0),
            ("dots", 0),
            ("dot", 5),
        ]

        for name, wait in priority:
            if self.tap_if_found(screen, name, wait):
                return True

        block_list = [item[0] for item in priority]
        if self.tap_cancel_if_safe(
            screen,
            cancel_name="cancel",
            block_if_found=block_list,
            extra_wait=5,
        ):
            return True

        return False