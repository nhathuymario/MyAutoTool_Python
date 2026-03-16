from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

from .config_manager import BASE_DIR, resolve_path


@dataclass
class MatchResult:
    x: int
    y: int
    score: float
    top_left: Tuple[int, int]
    bottom_right: Tuple[int, int]


class ImageMatcher:
    def __init__(self, debug_dir: Path | None = None):
        self.debug_dir = debug_dir or (BASE_DIR / "debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def load_template(self, template_path: str) -> np.ndarray:
        full_path = resolve_path(template_path)
        template = cv2.imread(str(full_path), cv2.IMREAD_COLOR)
        if template is None:
            raise RuntimeError(f"Không đọc được template: {full_path}")
        return template

    def crop_region(self, image: np.ndarray, region: Optional[Tuple[int, int, int, int]]) -> tuple[np.ndarray, tuple[int, int]]:
        if region is None:
            return image, (0, 0)
        left, top, width, height = region
        cropped = image[top: top + height, left: left + width]
        return cropped, (left, top)

    def find_template(
        self,
        screen_bgr: np.ndarray,
        template_path: str,
        threshold: float = 0.75,
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> Optional[MatchResult]:
        template = self.load_template(template_path)
        cropped, offset = self.crop_region(screen_bgr, region)

        result = cv2.matchTemplate(cropped, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < threshold:
            return None

        h, w = template.shape[:2]
        abs_x = max_loc[0] + offset[0] + w // 2
        abs_y = max_loc[1] + offset[1] + h // 2
        top_left = (max_loc[0] + offset[0], max_loc[1] + offset[1])
        bottom_right = (top_left[0] + w, top_left[1] + h)
        return MatchResult(abs_x, abs_y, float(max_val), top_left, bottom_right)

    def save_debug_image(self, image_bgr: np.ndarray, prefix: str = "capture") -> str:
        filename = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = self.debug_dir / filename
        cv2.imwrite(str(path), image_bgr)
        return str(path)

    def save_match_preview(self, image_bgr: np.ndarray, match: MatchResult, prefix: str = "match") -> str:
        preview = image_bgr.copy()
        cv2.rectangle(preview, match.top_left, match.bottom_right, (0, 255, 0), 2)
        cv2.putText(
            preview,
            f"score={match.score:.3f}",
            (match.top_left[0], max(20, match.top_left[1] - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )
        return self.save_debug_image(preview, prefix=prefix)
