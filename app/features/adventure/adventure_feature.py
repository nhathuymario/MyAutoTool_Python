from __future__ import annotations
import time
import win32api
import win32con
import win32gui

from app.features.base_feature import BaseFeature


class AdventureFeature(BaseFeature):
    key = "adventure"
    name = "Vượt ải"

    def __init__(self, adb, image_dir, logger=print):
        super().__init__(adb, image_dir, logger)
        self.last_zoom_time = 0

        # Tọa độ giữa cửa sổ giả lập theo CLIENT AREA
        self.zoom_x = 960
        self.zoom_y = 540

        # Từ khóa tìm cửa sổ LDPlayer
        self.window_keywords = ["LDPlayer", "dnplayer"]

    def _find_ld_window(self):
        found = []

        def enum_handler(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = win32gui.GetWindowText(hwnd) or ""
            lower_title = title.lower()
            if any(k.lower() in lower_title for k in self.window_keywords):
                found.append(hwnd)

        win32gui.EnumWindows(enum_handler, None)
        return found[0] if found else None

    def _send_ctrl_wheel(self, hwnd, steps: int = 8, delta: int = -120):
        if not hwnd:
            self.log("[Zoom] Không tìm thấy cửa sổ LDPlayer.")
            return False

        try:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            except Exception:
                pass

            try:
                win32gui.SetForegroundWindow(hwnd)
            except Exception:
                pass

            screen_x, screen_y = win32gui.ClientToScreen(hwnd, (self.zoom_x, self.zoom_y))
            lparam = win32api.MAKELONG(screen_x, screen_y)

            for _ in range(steps):
                wparam = win32con.MK_CONTROL | ((delta & 0xFFFF) << 16)
                win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
                win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, wparam, lparam)
                time.sleep(0.05)

            return True
        except Exception as e:
            self.log(f"[Zoom] Gửi Ctrl+scroll thất bại: {e}")
            return False

    def zoom_out(self):
        """Zoom trong cửa sổ LD, không dùng chuột máy tính"""
        self.log("[Action] Đang zoom out trong LDPlayer...")
        hwnd = self._find_ld_window()
        if self._send_ctrl_wheel(hwnd, steps=8, delta=-120):
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