from __future__ import annotations

from app.features.base_feature import BaseFeature
from app.features.adventure.stage_analyzer import StageAnalyzer


class AdventureFeature(BaseFeature):
    key = "adventure"
    name = "Vượt ải"

    def __init__(self, adb, image_dir, logger=print):
        super().__init__(adb, image_dir, logger)
        self.stage_analyzer = StageAnalyzer()

    def run_once(self) -> bool:
        screen = self.capture()

        # ===== UI flow trước =====
        priority = [
            ("skip", 0),
            ("next_stage", 0),
            ("exit", 0),
            ("victory", 0),
            ("claim", 0),
            ("tap", 0),
            ("battle1", 0),
            ("ready", 0),
            ("battle", 0),
            ("up", 0),
            ("dots", 0),
            ("dot", 10),
        ]

        for name, wait in priority:
            if self.tap_if_found(screen, name, wait):
                return True

        # ===== AI chọn ải =====
        node = self.stage_analyzer.choose_best_node(screen)

        if node:
            cx = node.x + node.w // 2
            cy = node.y + node.h // 2

            self.adb.tap(cx, cy)

            self.log(f"[AI] chọn ải: {node.state} ({cx},{cy})")
            return True

        # ===== Chỉ bấm cancel khi xung quanh / trên màn hình không còn nút khác =====
        block_cancel_if_found = [
            "skip",
            "next_stage",
            "exit",
            "victory",
            "claim",
            "tap",
            "battle1",
            "ready",
            "battle",
            "up",
            "dots",
            "dot",
        ]

        if self.tap_cancel_if_safe(
            screen,
            cancel_name="cancel",
            block_if_found=block_cancel_if_found,
            extra_wait=5,
        ):
            return True

        return False