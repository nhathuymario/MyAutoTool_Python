import os
import time
from typing import Any

from app.adb_client import AdbClient
from app.screen_capture import capture_screen
from app.image_match import find_template_center


class LdPlayerBot:
    def __init__(
        self,
        adb: AdbClient,
        screen_path: str,
        steps: list[dict[str, Any]],
        threshold: float = 0.85,
        scan_interval: float = 1.0,
        max_actions: int = 100,
    ):
        self.adb = adb
        self.screen_path = screen_path
        self.steps = steps
        self.threshold = threshold
        self.scan_interval = scan_interval
        self.max_actions = max_actions

        self.running = False
        self.total_actions = 0
        self.current_step_index = 0

    def log(self, message: str) -> None:
        print(message)

    def enabled_steps(self) -> list[dict[str, Any]]:
        return [step for step in self.steps if step.get("enabled", True)]

    def start(self) -> None:
        self.running = True
        self.total_actions = 0
        self.current_step_index = 0
        self.log("Bot started")

        steps = self.enabled_steps()
        if not steps:
            self.log("No enabled steps")
            return

        while self.running:
            if self.total_actions >= self.max_actions:
                self.log(f"Reached max actions: {self.max_actions}")
                break

            steps = self.enabled_steps()
            if not steps:
                self.log("No enabled steps")
                break

            step = steps[self.current_step_index % len(steps)]
            self.run_step(step)

            time.sleep(self.scan_interval)

        self.running = False
        self.log("Bot stopped")

    def stop(self) -> None:
        self.running = False

    def run_step(self, step: dict[str, Any]) -> None:
        step_name = step["name"]
        image_path = step["image"]

        if not os.path.exists(image_path):
            self.log(f"[{step_name}] Missing template: {image_path}")
            self.current_step_index += 1
            return

        try:
            capture_screen(self.adb, self.screen_path)
            match = find_template_center(
                self.screen_path,
                image_path,
                self.threshold
            )

            if match is None:
                self.log(f"[{step_name}] Not found")
                return

            x, y, score = match
            self.log(f"[{step_name}] Found at ({x}, {y}) score={score:.3f}")

            out, err, code = self.adb.tap(x, y)
            if code == 0:
                self.total_actions += 1
                self.log(f"[{step_name}] Tapped | total={self.total_actions}")
                self.current_step_index += 1
            else:
                self.log(f"[{step_name}] Tap failed: {err or out}")

        except Exception as exc:
            self.log(f"[{step_name}] Error: {exc}")