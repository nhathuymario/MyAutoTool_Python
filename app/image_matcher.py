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
    gray: bool = True,
    zoom_scale: float = 1.0,
) -> Optional[MatchResult]:
    path = Path(template_path)
    if not path.exists():
        raise RuntimeError(f"Không tìm thấy template: {path}")

    template = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if template is None:
        raise RuntimeError(f"Không đọc được template: {path}")

    src = screen
    tpl = template

    # Chuyển grayscale nếu bật
    if gray:
        if len(src.shape) == 3:
            src = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
        if len(tpl.shape) == 3:
            tpl = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)

    # Zoom ảnh xử lý để match dễ hơn
    if zoom_scale != 1.0:
        src = cv2.resize(
            src,
            None,
            fx=zoom_scale,
            fy=zoom_scale,
            interpolation=cv2.INTER_LINEAR,
        )
        tpl = cv2.resize(
            tpl,
            None,
            fx=zoom_scale,
            fy=zoom_scale,
            interpolation=cv2.INTER_LINEAR,
        )

    result = cv2.matchTemplate(src, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    h, w = tpl.shape[:2]

    # Tọa độ tìm được đang ở ảnh đã zoom -> chia ngược về tọa độ thật
    real_x = int((max_loc[0] + w // 2) / zoom_scale)
    real_y = int((max_loc[1] + h // 2) / zoom_scale)
    real_w = int(w / zoom_scale)
    real_h = int(h / zoom_scale)

    return MatchResult(
        x=real_x,
        y=real_y,
        score=float(max_val),
        width=real_w,
        height=real_h,
    )


class ImageMatcher:
    def find_template(
        self,
        screen=None,
        template_path: str = "",
        threshold: float = 0.75,
        gray: bool = True,
        zoom_scale: float = 1.0,
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
            zoom_scale=zoom_scale,
        )

    def save_debug_image(self, screen, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), screen)