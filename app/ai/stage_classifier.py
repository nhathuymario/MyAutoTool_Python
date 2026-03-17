from __future__ import annotations

import cv2
import numpy as np
import joblib


class StageClassifier:

    def __init__(self, model_path="stage_model.pkl"):
        self.model = None
        try:
            self.model = joblib.load(model_path)
            print("[AI] model loaded")
        except Exception:
            print("[AI] chưa có model, fallback rule-based")

    def extract_features(self, img):
        img = cv2.resize(img, (64, 64))

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)

        return np.hstack([hist, brightness])

    def predict(self, img):
        if self.model is None:
            return None

        feat = self.extract_features(img)
        pred = self.model.predict([feat])[0]
        return pred