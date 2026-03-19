from __future__ import annotations

import cv2
import numpy as np
import os
import time
from dataclasses import dataclass
from typing import List, Optional

from app.ai.stage_classifier import StageClassifier


@dataclass
class StageNode:
    x: int
    y: int
    w: int
    h: int
    state: str


class StageAnalyzer:

    def __init__(self):
        self.classifier = StageClassifier()

    def analyze(self, screen) -> List[StageNode]:
        gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        nodes = []

        for cnt in contours:
            area = cv2.contourArea(cnt)

            if area < 1000 or area > 50000:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            if w < 30 or h < 20:
                continue

            roi = screen[y:y + h, x:x + w]

            state = self.classifier.predict(roi)

            # fallback rule
            if state is None:
                state = "normal"

            nodes.append(StageNode(x, y, w, h, state))

        return nodes

    # def choose_best_node(self, screen) -> Optional[StageNode]:
    #     nodes = self.analyze(screen)

    #     if not nodes:
    #         return None

    #     current = [n for n in nodes if n.state == "current"]
    #     if current:
    #         return current[0]

    #     normal = [n for n in nodes if n.state == "normal"]
    #     if normal:
    #         return normal[0]

    #     completed = [n for n in nodes if n.state == "completed"]
    #     if completed:
    #         return completed[0]

        return None