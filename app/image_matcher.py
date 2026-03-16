from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


@dataclass
class MatchResult:
    x: int
    y: int
    score: float
    width: int
    height: int


def find_template(
    screen: np.ndarray,
    template_path: str,
    threshold: float = 0.75,
    gray: bool = False,
) -> Optional[MatchResult]:
    path = Path(template_path)
    if not path.exists():
        raise RuntimeError(f"Không tìm thấy template: {path}")

    template = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if template is None:
        raise RuntimeError(f"Không đọc được template: {path}")

    src = screen
    tpl = template

    if gray:
        src = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        tpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(src, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    h, w = template.shape[:2]
    return MatchResult(
        x=max_loc[0] + w // 2,
        y=max_loc[1] + h // 2,
        score=float(max_val),
        width=w,
        height=h,
    )


class ImageMatcher:
    def find_template(
        self,
        screen=None,
        template_path: str = "",
        threshold: float = 0.75,
        gray: bool = False,
        screen_bgr=None,
    ) -> Optional[MatchResult]:
        src = screen_bgr if screen_bgr is not None else screen
        if src is None:
            raise ValueError("Thiếu ảnh đầu vào: screen hoặc screen_bgr")

        return find_template(
            screen=src,
            template_path=template_path,
            threshold=threshold,
            gray=gray,
        )

    def save_debug_image(self, screen, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), screen)