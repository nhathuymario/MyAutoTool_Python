import os
import cv2
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import joblib

DATASET_DIR = "app/dataset"


def extract_features(img):
    img = cv2.resize(img, (64, 64))

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
    hist = cv2.normalize(hist, hist).flatten()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)

    return np.hstack([hist, brightness])


X, y = [], []

for label in ["current", "completed", "normal"]:
    path = os.path.join(DATASET_DIR, label)

    if not os.path.exists(path):
        continue

    for file in os.listdir(path):
        img_path = os.path.join(path, file)
        img = cv2.imread(img_path)

        if img is None:
            continue

        feat = extract_features(img)
        X.append(feat)
        y.append(label)

model = KNeighborsClassifier(n_neighbors=3)
model.fit(X, y)

joblib.dump(model, "stage_model.pkl")

print("✅ Train xong → stage_model.pkl")