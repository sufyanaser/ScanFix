"""Deterministic document geometry helpers for ScanFix V0.1.

Scope:
- page boundary detection
- four-corner ordering
- perspective rectification
- small-angle deskew

No OCR, no generative processing, no content reconstruction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class DetectionResult:
    corners: np.ndarray | None
    confidence: float
    needs_review: bool
    reason: str


def order_points(points: Iterable[Iterable[float]]) -> np.ndarray:
    """Return corners ordered TL, TR, BR, BL."""
    pts = np.asarray(points, dtype=np.float32)
    if pts.shape != (4, 2):
        raise ValueError("Expected exactly four 2D points")

    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(-1)

    ordered[0] = pts[np.argmin(sums)]   # TL
    ordered[2] = pts[np.argmax(sums)]   # BR
    ordered[1] = pts[np.argmin(diffs)]  # TR
    ordered[3] = pts[np.argmax(diffs)]  # BL
    return ordered


def _resize_for_detection(image: np.ndarray, max_dim: int = 1800) -> tuple[np.ndarray, float]:
    h, w = image.shape[:2]
    scale = 1.0
    longest = max(h, w)
    if longest > max_dim:
        scale = max_dim / float(longest)
        resized = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
        return resized, scale
    return image.copy(), scale


def _quad_score(quad: np.ndarray, image_area: float) -> tuple[float, float]:
    area = abs(cv2.contourArea(quad.astype(np.float32)))
    area_ratio = area / max(image_area, 1.0)

    rect = cv2.minAreaRect(quad.astype(np.float32))
    box_area = max(rect[1][0] * rect[1][1], 1.0)
    rectangularity = min(area / box_area, 1.0)

    # Favor a page occupying a meaningful part of the frame and having a stable quadrilateral.
    area_score = float(np.clip((area_ratio - 0.18) / 0.62, 0.0, 1.0))
    confidence = 0.65 * area_score + 0.35 * rectangularity
    return confidence, area_ratio


def detect_document(image: np.ndarray, min_confidence: float = 0.72) -> DetectionResult:
    """Detect the most plausible page quadrilateral.

    Returns a safe failure when no strong quadrilateral is found.
    """
    if image is None or image.size == 0:
        return DetectionResult(None, 0.0, True, "empty-image")

    work, scale = _resize_for_detection(image)
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY) if work.ndim == 3 else work.copy()

    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]

    image_area = float(work.shape[0] * work.shape[1])
    best_quad = None
    best_confidence = 0.0
    best_area_ratio = 0.0

    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue

        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) != 4 or not cv2.isContourConvex(approx):
            continue

        quad = approx.reshape(4, 2).astype(np.float32)
        confidence, area_ratio = _quad_score(quad, image_area)

        if confidence > best_confidence:
            best_quad = quad
            best_confidence = confidence
            best_area_ratio = area_ratio

    if best_quad is None:
        return DetectionResult(None, 0.0, True, "no-quadrilateral")

    corners = order_points(best_quad / scale)
    needs_review = best_confidence < min_confidence

    reason = "ok"
    if best_area_ratio < 0.25:
        reason = "page-too-small-or-ambiguous"
        needs_review = True
    elif needs_review:
        reason = "low-confidence"

    return DetectionResult(
        corners=corners,
        confidence=round(float(best_confidence), 4),
        needs_review=needs_review,
        reason=reason,
    )


def perspective_rectify(image: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Rectify a planar page from four source corners."""
    pts = order_points(corners)
    tl, tr, br, bl = pts

    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)

    width = max(int(round(max(width_top, width_bottom))), 2)
    height = max(int(round(max(height_left, height_right))), 2)

    dst = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(pts, dst)
    return cv2.warpPerspective(
        image,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def estimate_skew_angle(image: np.ndarray, max_abs_angle: float = 7.0) -> float:
    """Estimate small residual text/page skew in degrees.

    Only near-horizontal Hough segments are used. Returns 0 when evidence is weak.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(gray, 50, 150)

    min_len = max(40, int(min(image.shape[:2]) * 0.12))
    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 1800.0,
        threshold=60,
        minLineLength=min_len,
        maxLineGap=12,
    )
    if lines is None:
        return 0.0

    angles: list[float] = []
    for line in lines[:, 0]:
        x1, y1, x2, y2 = map(float, line)
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
        while angle <= -90:
            angle += 180
        while angle > 90:
            angle -= 180
        if abs(angle) <= max_abs_angle:
            angles.append(float(angle))

    if len(angles) < 3:
        return 0.0

    median = float(np.median(np.asarray(angles, dtype=np.float32)))
    return round(median, 3)


def rotate_expand(image: np.ndarray, angle_deg: float) -> np.ndarray:
    """Rotate without clipping by expanding the output canvas."""
    if abs(angle_deg) < 1e-6:
        return image.copy()

    h, w = image.shape[:2]
    center = (w / 2.0, h / 2.0)
    matrix = cv2.getRotationMatrix2D(center, angle_deg, 1.0)

    cos_v = abs(matrix[0, 0])
    sin_v = abs(matrix[0, 1])
    new_w = int(np.ceil((h * sin_v) + (w * cos_v)))
    new_h = int(np.ceil((h * cos_v) + (w * sin_v)))

    matrix[0, 2] += (new_w / 2.0) - center[0]
    matrix[1, 2] += (new_h / 2.0) - center[1]

    border = 255 if image.ndim == 2 else (255, 255, 255)
    return cv2.warpAffine(
        image,
        matrix,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=border,
    )


def deskew(image: np.ndarray, max_abs_angle: float = 7.0) -> tuple[np.ndarray, float]:
    """Estimate and correct small residual skew."""
    angle = estimate_skew_angle(image, max_abs_angle=max_abs_angle)
    if abs(angle) < 0.15:
        return image.copy(), 0.0
    return rotate_expand(image, -angle), angle
