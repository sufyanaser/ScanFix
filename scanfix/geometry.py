"""Deterministic document geometry helpers for ScanFix V0.2.

Scope:
- conservative page boundary detection
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

from scanfix.segmentation import detect_bright_page_candidate


@dataclass(frozen=True)
class DetectionResult:
    corners: np.ndarray | None
    confidence: float
    needs_review: bool
    reason: str
    area_ratio: float = 0.0


def order_points(points: Iterable[Iterable[float]]) -> np.ndarray:
    """Return corners ordered TL, TR, BR, BL."""
    pts = np.asarray(points, dtype=np.float32)
    if pts.shape != (4, 2):
        raise ValueError("Expected exactly four 2D points")

    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = pts.sum(axis=1)
    diffs = np.diff(pts, axis=1).reshape(-1)

    ordered[0] = pts[np.argmin(sums)]
    ordered[2] = pts[np.argmax(sums)]
    ordered[1] = pts[np.argmin(diffs)]
    ordered[3] = pts[np.argmax(diffs)]
    return ordered


def _resize_for_detection(image: np.ndarray, max_dim: int = 1800) -> tuple[np.ndarray, float]:
    h, w = image.shape[:2]
    scale = 1.0
    longest = max(h, w)

    if longest > max_dim:
        scale = max_dim / float(longest)
        resized = cv2.resize(
            image,
            (round(w * scale), round(h * scale)),
            interpolation=cv2.INTER_AREA,
        )
        return resized, scale

    return image.copy(), scale


def _border_proximity(quad: np.ndarray, width: int, height: int) -> float:
    """Return how strongly a quad hugs all image borders.

    Full-frame contours are common false positives. A high value is a mild penalty,
    not an automatic rejection, because some documents legitimately fill the frame.
    """
    pts = order_points(quad)
    margin_x = max(width * 0.03, 1.0)
    margin_y = max(height * 0.03, 1.0)

    close = 0
    for x, y in pts:
        if x <= margin_x or x >= width - margin_x:
            close += 1
        if y <= margin_y or y >= height - margin_y:
            close += 1

    return min(close / 8.0, 1.0)


def _quad_score(
    quad: np.ndarray,
    image_area: float,
    width: int,
    height: int,
) -> tuple[float, float]:
    area = abs(cv2.contourArea(quad.astype(np.float32)))
    area_ratio = area / max(image_area, 1.0)

    rect = cv2.minAreaRect(quad.astype(np.float32))
    box_area = max(rect[1][0] * rect[1][1], 1.0)
    rectangularity = min(area / box_area, 1.0)

    area_score = float(np.clip((area_ratio - 0.16) / 0.68, 0.0, 1.0))
    border_penalty = 0.15 * _border_proximity(quad, width, height)

    confidence = (0.62 * area_score) + (0.38 * rectangularity) - border_penalty
    confidence = float(np.clip(confidence, 0.0, 1.0))
    return confidence, area_ratio


def _edge_variants(gray: np.ndarray) -> list[np.ndarray]:
    """Produce a small deterministic set of edge maps for difficult phone photos."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    variants: list[np.ndarray] = []
    for low, high in ((35, 105), (50, 150), (75, 200)):
        edges = cv2.Canny(blur, low, high)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        variants.append(edges)

    # Contrast-normalized pass helps with weak page/background separation.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(blur)
    edges = cv2.Canny(clahe, 45, 135)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    variants.append(edges)

    return variants


def detect_document(image: np.ndarray, min_confidence: float = 0.72) -> DetectionResult:
    """Detect the most plausible page quadrilateral.

    The detector tries a few conservative edge maps and returns a safe review state
    when confidence is insufficient.
    """
    if image is None or image.size == 0:
        return DetectionResult(None, 0.0, True, "empty-image", 0.0)

    work, scale = _resize_for_detection(image)
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY) if work.ndim == 3 else work.copy()

    image_area = float(work.shape[0] * work.shape[1])
    height, width = work.shape[:2]

    best_quad: np.ndarray | None = None
    best_confidence = 0.0
    best_area_ratio = 0.0

    for edges in _edge_variants(gray):
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]

        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            if perimeter <= 0:
                continue

            for epsilon_ratio in (0.015, 0.02, 0.025):
                approx = cv2.approxPolyDP(
                    contour,
                    epsilon_ratio * perimeter,
                    True,
                )
                if len(approx) != 4 or not cv2.isContourConvex(approx):
                    continue

                quad = approx.reshape(4, 2).astype(np.float32)
                confidence, area_ratio = _quad_score(
                    quad,
                    image_area,
                    width,
                    height,
                )

                if confidence > best_confidence:
                    best_quad = quad
                    best_confidence = confidence
                    best_area_ratio = area_ratio

    edge_is_weak = (
        best_quad is None
        or best_area_ratio < 0.22
        or best_confidence < min_confidence
    )

    if edge_is_weak:
        fallback = detect_bright_page_candidate(image)
        if fallback.corners is not None:
            return DetectionResult(
                corners=fallback.corners,
                confidence=fallback.confidence,
                needs_review=fallback.needs_review,
                reason=fallback.reason,
                area_ratio=fallback.area_ratio,
            )

    if best_quad is None:
        return DetectionResult(None, 0.0, True, "no-quadrilateral", 0.0)

    corners = order_points(best_quad / scale)
    needs_review = best_confidence < min_confidence

    reason = "ok"
    if best_area_ratio < 0.22:
        reason = "page-too-small-or-ambiguous"
        needs_review = True
    elif best_area_ratio > 0.985:
        reason = "full-frame-ambiguous"
        needs_review = True
    elif needs_review:
        reason = "low-confidence"

    return DetectionResult(
        corners=corners,
        confidence=round(float(best_confidence), 4),
        needs_review=needs_review,
        reason=reason,
        area_ratio=round(float(best_area_ratio), 4),
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

    return rotate_expand(image, angle), angle
