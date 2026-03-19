from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import cv2
import numpy as np


@dataclass
class MatchResult:
    x: int
    y: int
    score: float
    width: int
    height: int


def _load_template(template_path: str) -> np.ndarray:
    path = Path(template_path)
    if not path.exists():
        raise RuntimeError(f"Không tìm thấy template: {path}")

    template = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if template is None:
        raise RuntimeError(f"Không đọc được template: {path}")

    return template


def _crop_region(screen: np.ndarray, region: Optional[tuple[int, int, int, int]]):
    if region is None:
        return screen, 0, 0

    x1, y1, x2, y2 = region
    h, w = screen.shape[:2]

    x1 = max(0, min(x1, w - 1))
    y1 = max(0, min(y1, h - 1))
    x2 = max(x1 + 1, min(x2, w))
    y2 = max(y1 + 1, min(y2, h))

    cropped = screen[y1:y2, x1:x2]
    return cropped, x1, y1


def _prepare_image(img: np.ndarray, gray: bool = True, use_edge: bool = False) -> np.ndarray:
    out = img

    if gray and len(out.shape) == 3:
        out = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)

    if use_edge:
        if len(out.shape) == 3:
            out = cv2.cvtColor(out, cv2.COLOR_BGR2GRAY)
        out = cv2.GaussianBlur(out, (3, 3), 0)
        out = cv2.Canny(out, 60, 160)

    return out


def _resize_keep_valid(img: np.ndarray, scale: float) -> np.ndarray:
    if scale == 1.0:
        return img

    h, w = img.shape[:2]
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)


def _run_match(
    screen_proc: np.ndarray,
    template_proc: np.ndarray,
) -> tuple[float, tuple[int, int], int, int] | None:
    sh, sw = screen_proc.shape[:2]
    th, tw = template_proc.shape[:2]

    if th <= 0 or tw <= 0:
        return None
    if th > sh or tw > sw:
        return None

    result = cv2.matchTemplate(screen_proc, template_proc, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return float(max_val), max_loc, tw, th


def find_template(
    screen: np.ndarray,
    template_path: str,
    threshold: float = 0.75,
    gray: bool = True,
    zoom_scale: float = 1.0,
    region: Optional[tuple[int, int, int, int]] = None,
    multi_scale: bool = False,
    scales: Optional[Iterable[float]] = None,
    use_edge: bool = False,
) -> Optional[MatchResult]:
    """
    Tìm 1 kết quả tốt nhất.

    region: (x1, y1, x2, y2)
    multi_scale=True: thử nhiều scale cho template
    zoom_scale: giữ tương thích code cũ, phóng to cả screen/template trước khi match
    use_edge=True: match theo cạnh, hợp icon nhỏ
    """
    template = _load_template(template_path)
    src, offset_x, offset_y = _crop_region(screen, region)

    if zoom_scale != 1.0:
        src = _resize_keep_valid(src, zoom_scale)
        template = _resize_keep_valid(template, zoom_scale)

    src_proc = _prepare_image(src, gray=gray, use_edge=use_edge)

    if scales is None:
        if multi_scale:
            scales = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]
        else:
            scales = [1.0]

    best_score = -1.0
    best_loc = None
    best_w = 0
    best_h = 0
    best_scale = 1.0

    for scale in scales:
        tpl_scaled = _resize_keep_valid(template, scale)
        tpl_proc = _prepare_image(tpl_scaled, gray=gray, use_edge=use_edge)

        matched = _run_match(src_proc, tpl_proc)
        if matched is None:
            continue

        score, max_loc, tw, th = matched
        if score > best_score:
            best_score = score
            best_loc = max_loc
            best_w = tw
            best_h = th
            best_scale = scale

    if best_loc is None or best_score < threshold:
        return None

    cx = best_loc[0] + best_w // 2
    cy = best_loc[1] + best_h // 2

    # nếu đã zoom_scale thì trả ngược về tọa độ ảnh thật
    real_x = int(cx / zoom_scale) + offset_x
    real_y = int(cy / zoom_scale) + offset_y
    real_w = max(1, int(best_w / zoom_scale))
    real_h = max(1, int(best_h / zoom_scale))

    return MatchResult(
        x=real_x,
        y=real_y,
        score=float(best_score),
        width=real_w,
        height=real_h,
    )


def find_all_templates(
    screen: np.ndarray,
    template_path: str,
    threshold: float = 0.75,
    gray: bool = True,
    region: Optional[tuple[int, int, int, int]] = None,
    use_edge: bool = False,
    max_results: int = 20,
    min_distance: int = 10,
) -> list[MatchResult]:
    """
    Tìm nhiều điểm match của cùng 1 template.
    Hữu ích khi muốn tìm tất cả node level trên map.
    """
    template = _load_template(template_path)
    src, offset_x, offset_y = _crop_region(screen, region)

    src_proc = _prepare_image(src, gray=gray, use_edge=use_edge)
    tpl_proc = _prepare_image(template, gray=gray, use_edge=use_edge)

    matched = _run_match(src_proc, tpl_proc)
    if matched is None:
        return []

    th, tw = tpl_proc.shape[:2]
    result = cv2.matchTemplate(src_proc, tpl_proc, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(result >= threshold)

    raw_matches: list[MatchResult] = []
    for y, x in zip(ys, xs):
        cx = x + tw // 2 + offset_x
        cy = y + th // 2 + offset_y
        score = float(result[y, x])
        raw_matches.append(MatchResult(cx, cy, score, tw, th))

    raw_matches.sort(key=lambda m: m.score, reverse=True)

    filtered: list[MatchResult] = []
    for m in raw_matches:
        too_close = False
        for kept in filtered:
            if abs(m.x - kept.x) < min_distance and abs(m.y - kept.y) < min_distance:
                too_close = True
                break
        if not too_close:
            filtered.append(m)
        if len(filtered) >= max_results:
            break

    return filtered


def find_best_template_from_list(
    screen: np.ndarray,
    template_paths: list[str],
    threshold: float = 0.75,
    gray: bool = True,
    region: Optional[tuple[int, int, int, int]] = None,
    multi_scale: bool = False,
    scales: Optional[Iterable[float]] = None,
    use_edge: bool = False,
) -> tuple[Optional[str], Optional[MatchResult]]:
    """
    So nhiều template, lấy template nào khớp mạnh nhất.
    Rất hợp cho level1/level2/level3/level6.
    """
    best_name: Optional[str] = None
    best_match: Optional[MatchResult] = None

    for path in template_paths:
        try:
            match = find_template(
                screen=screen,
                template_path=path,
                threshold=threshold,
                gray=gray,
                region=region,
                multi_scale=multi_scale,
                scales=scales,
                use_edge=use_edge,
            )
        except Exception:
            continue

        if match is None:
            continue

        if best_match is None or match.score > best_match.score:
            best_match = match
            best_name = path

    return best_name, best_match


class ImageMatcher:
    def find_template(
        self,
        screen=None,
        template_path: str = "",
        threshold: float = 0.75,
        gray: bool = True,
        zoom_scale: float = 1.0,
        screen_bgr=None,
        region: Optional[tuple[int, int, int, int]] = None,
        multi_scale: bool = False,
        scales: Optional[Iterable[float]] = None,
        use_edge: bool = False,
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
            region=region,
            multi_scale=multi_scale,
            scales=scales,
            use_edge=use_edge,
        )

    def find_all_templates(
        self,
        screen=None,
        template_path: str = "",
        threshold: float = 0.75,
        gray: bool = True,
        screen_bgr=None,
        region: Optional[tuple[int, int, int, int]] = None,
        use_edge: bool = False,
        max_results: int = 20,
        min_distance: int = 10,
    ) -> list[MatchResult]:
        src = screen_bgr if screen_bgr is not None else screen
        if src is None:
            raise ValueError("Thiếu ảnh đầu vào: screen hoặc screen_bgr")

        return find_all_templates(
            screen=src,
            template_path=template_path,
            threshold=threshold,
            gray=gray,
            region=region,
            use_edge=use_edge,
            max_results=max_results,
            min_distance=min_distance,
        )

    def save_debug_image(self, screen, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), screen)