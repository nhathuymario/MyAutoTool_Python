from __future__ import annotations

from app.features.base_feature import BaseFeature


class TowerFeature(BaseFeature):
    key = "tower"
    name = "Vượt Tháp"

    def run_once(self) -> bool:
        try:
            screen = self.capture()
        except Exception as e:
            self.log(f"[{self.name}] [capture] lỗi: {e}")
            return False

        actions = [
            ("skip", 0),
            ("next_stage", 0),
            ("exit", 0),
            ("victorythap", 0),

            # ===== reward =====
            ("claim", 0),

            # ===== battle flow =====
            ("tap", 0),
            ("battle1", 0),
            ("ready", 0),
            ("battle", 0),

            # ===== map control =====
            ("up", 0),
        ]

        for name, wait_time in actions:
            if self.tap_if_found(screen, name, extra_wait=wait_time):
                return True

        return False