"""Conservative brightness-segmentation fallback for page detection.

This module does not alter the document. It only proposes a page quadrilateral when
edge-only detection fails. Ambiguous partial, stacked, or cropped pages are routed
to manual review.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class SegmentationCandidate:
    corners: np.ndarray | None
    confidence: float
    needs_review: bool
    reason: str
    area_ratio: float


def _order_points(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32)
    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(-1)
    ordered[0] = pts[np.argmin(sums)]
    ordered[2] = pts[np.argmax(sums)]
    ordered[1] = pts[np.argmin(diffs)]
    ordered[3] = pts[np.argmax(diffs)]
    return ordered


def _resize(image: np.ndarray, max_dim: int = 1800) -> tuple[np.ndarray, float]:
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return image.copy(), 1.0

    scale = max_dim / float(longest)
    out = cv2.resize(
        image,
        (round(w * scale), round(h * scale)),
        interpolation=cv2.INTER_AREA,
    )
    return out, scale


def _border_sides_touched(corners: np.ndarray, width: int, height: int) -> int:
    pts = _order_points(corners)
    mx = max(width * 0.025, 2.0)
    my = max(height * 0.025, 2.0)

    left = bool(np.any(pts[:, 0] <= mx))
    right = bool(np.any(pts[:, 0] >= width - mx))
    top = bool(np.any(pts[:, 1] <= my))
    bottom = bool(np.any(pts[:, 1] >= height - my))
    return int(left) + int(right) + int(top) + int(bottom)


def _stacked_page_hint(gray: np.ndarray) -> bool:
    """Detect repeated long horizontal edges low in the frame.

    This is intentionally only a hint for full-frame bright candidates. It helps
    separate a single page from a stack where another sheet is visible underneath.
    """
    h, w = gray.shape[:2]
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 150)
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180.0,
        threshold=80,
        minLineLength=max(80, int(w * 0.55)),
        maxLineGap=30,
    )
    if lines is None:
        return False

    ys: list[float] = []
    for x1, y1, x2, y2 in lines[:, 0]:
        angle = abs(np.degrees(np.arctan2(float(y2 - y1), float(x2 - x1))))
        if angle <= 5.0:
            y = (float(y1) + float(y2)) / 2.0
            if y >= h * 0.70:
                ys.append(y)

    if len(ys) < 2:
        return False

    ys.sort()
    clusters: list[list[float]] = []
    gap = max(12.0, h * 0.025)

    for y in ys:
        if not clusters or abs(y - np.mean(clusters[-1])) > gap:
            clusters.append([y])
        else:
            clusters[-1].append(y)

    centers = [float(np.mean(c)) for c in clusters]
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            if abs(centers[j] - centers[i]) >= h * 0.055:
                return True

    return False


def detect_bright_page_candidate(image: np.ndarray) -> SegmentationCandidate:
    if image is None or image.size == 0:
        return SegmentationCandidate(None, 0.0, True, "no-segmentation-candidate", 0.0)

    work, scale = _resize(image)
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY) if work.ndim == 3 else work.copy()
    blur = cv2.GaussianBlur(gray, (7, 7), 0)

    h, w = gray.shape[:2]
    image_area = float(h * w)
    masks: list[np.ndarray] = []

    _, otsu = cv2.threshold(
        blur,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    masks.append(otsu)

    for threshold in (100, 120, 140, 160, 180, 200):
        _, mask = cv2.threshold(blur, threshold, 255, cv2.THRESH_BINARY)
        masks.append(mask)

    kernel_size = max(9, round(min(h, w) * 0.015))
    if kernel_size % 2 == 0:
        kernel_size += 1

    close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (kernel_size, kernel_size),
    )
    open_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    candidates: list[tuple[float, np.ndarray]] = []

    for mask in masks:
        cleaned = cv2.morphologyEx(
            mask,
            cv2.MORPH_CLOSE,
            close_kernel,
            iterations=2,
        )
        cleaned = cv2.morphologyEx(
            cleaned,
            cv2.MORPH_OPEN,
            open_kernel,
            iterations=1,
        )

        contours, _ = cv2.findContours(
            cleaned,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        for contour in contours:
            area = cv2.contourArea(contour)
            area_ratio = area / max(image_area, 1.0)
            if area_ratio < 0.15:
                continue

            hull = cv2.convexHull(contour)
            perimeter = cv2.arcLength(hull, True)
            if perimeter <= 0:
                continue

            for epsilon_ratio in (0.01, 0.02, 0.03, 0.05):
                approx = cv2.approxPolyDP(
                    hull,
                    epsilon_ratio * perimeter,
                    True,
                )
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    quad = approx.reshape(4, 2).astype(np.float32)
                    candidates.append((area_ratio, quad))
                    break

    if not candidates:
        return SegmentationCandidate(None, 0.0, True, "no-segmentation-candidate", 0.0)

    area_ratio, quad = max(candidates, key=lambda item: item[0])
    corners = _order_points(quad)
    touched = _border_sides_touched(corners, w, h)

    if area_ratio >= 0.97:
        # A full-frame bright/gray field is not enough to call something a document.
        # Require visible content/texture evidence so blank walls or uniform frames
        # do not become false-positive pages.
        contrast_std = float(gray.std())
        edge_density = float(
            np.count_nonzero(cv2.Canny(gray, 50, 150))
            / max(gray.size, 1)
        )
        if contrast_std < 12.0 and edge_density < 0.002:
            return SegmentationCandidate(
                None,
                0.0,
                True,
                "no-document-content",
                round(float(area_ratio), 4),
            )

        if _stacked_page_hint(gray):
            return SegmentationCandidate(
                _order_points(corners / scale),
                0.68,
                True,
                "stacked-pages-ambiguous",
                round(float(area_ratio), 4),
            )

        return SegmentationCandidate(
            _order_points(corners / scale),
            0.80,
            False,
            "full-frame-document",
            round(float(area_ratio), 4),
        )

    if touched >= 2:
        return SegmentationCandidate(
            _order_points(corners / scale),
            0.66,
            True,
            "partial-page-or-cropped",
            round(float(area_ratio), 4),
        )

    if area_ratio >= 0.35:
        return SegmentationCandidate(
            _order_points(corners / scale),
            0.78,
            False,
            "segmentation-page",
            round(float(area_ratio), 4),
        )

    return SegmentationCandidate(
        _order_points(corners / scale),
        0.55,
        True,
        "segmentation-low-confidence",
        round(float(area_ratio), 4),
    )
