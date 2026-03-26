from __future__ import annotations

from app.features.base_feature import BaseFeature


class AllianceFeature(BaseFeature):
    key = "Alliance"
    name = "Vượt Alliance"

    def run_once(self) -> bool:
        try:
            screen = self.capture()
        except Exception as e:
            self.log(f"[{self.name}] [capture] lỗi: {e}")
            return False

        actions = [
            ("tap1", 0),
            ("chest", 0),
            ("openchest", 0),
            ("oke", 0),
            ("exit", 0),

            # ===== reward =====
            ("battlealliance", 0),

            # ===== battle flow =====
            # ===== map control =====
        ]

        for name, wait_time in actions:
            if self.tap_if_found(screen, name, extra_wait=wait_time):
                return True

        return False