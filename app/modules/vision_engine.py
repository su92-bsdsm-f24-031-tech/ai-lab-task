"""OpenCV-based image features as JSON-serializable dicts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np


def extract_features(image_path: str | Path) -> dict[str, Any] | None:
    path = Path(image_path)
    if not path.is_file():
        return None

    img = cv2.imread(str(path))
    if img is None:
        return None

    h, w = img.shape[:2]
    max_side = 800
    scale = min(1.0, max_side / max(h, w))
    if scale < 1.0:
        img = cv2.resize(
            img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )
        h, w = img.shape[:2]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
    hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
    hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])
    cv2.normalize(hist_h, hist_h, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist_s, hist_s, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    cv2.normalize(hist_v, hist_v, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

    pixels = hsv.reshape((-1, 3)).astype(np.float32)
    k = min(5, len(pixels))
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )
    dominant = centers.astype(np.float32).tolist()

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    edge_ratio = float(np.mean(edges > 0))

    return {
        "size": [int(w), int(h)],
        "hist_h": hist_h.flatten().astype(float).tolist(),
        "hist_s": hist_s.flatten().astype(float).tolist(),
        "hist_v": hist_v.flatten().astype(float).tolist(),
        "dominant_hsv": dominant,
        "edge_ratio": edge_ratio,
    }


def histogram_similarity(a: dict | None, b: dict | None) -> float:
    """Return similarity in [0, 1] from stored vision feature dicts."""
    if not a or not b:
        return 0.5

    def _corr(x: list, y: list) -> float:
        xa = np.array(x, dtype=np.float64)
        ya = np.array(y, dtype=np.float64)
        if xa.size != ya.size or xa.size == 0:
            return 0.5
        if np.allclose(xa, ya, rtol=0, atol=1e-9):
            return 1.0
        c = np.corrcoef(xa, ya)[0, 1]
        if np.isnan(c):
            return 0.5
        return float(np.clip((c + 1) / 2, 0.0, 1.0))

    s_h = _corr(a.get("hist_h") or [], b.get("hist_h") or [])
    s_s = _corr(a.get("hist_s") or [], b.get("hist_s") or [])
    s_v = _corr(a.get("hist_v") or [], b.get("hist_v") or [])
    return float(np.clip((s_h + s_s + s_v) / 3.0, 0.0, 1.0))
