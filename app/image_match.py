import os
from typing import Optional, Tuple

import cv2
import numpy as np


def find_template_center(
    screen_path: str,
    template_path: str,
    threshold: float = 0.85
) -> Optional[Tuple[int, int, float]]:
    if not os.path.exists(screen_path):
        raise FileNotFoundError(f"Screen not found: {screen_path}")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    screen = cv2.imread(screen_path, cv2.IMREAD_COLOR)
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    if screen is None:
        raise ValueError(f"Cannot read screen image: {screen_path}")
    if template is None:
        raise ValueError(f"Cannot read template image: {template_path}")

    result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    template_h, template_w = template.shape[:2]
    center_x = max_loc[0] + template_w // 2
    center_y = max_loc[1] + template_h // 2

    return center_x, center_y, float(max_val)