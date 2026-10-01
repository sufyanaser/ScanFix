from __future__ import annotations

import cv2
import numpy as np

from scanfix.geometry import (
    deskew,
    detect_document,
    order_points,
    perspective_rectify,
    rotate_expand,
)


def _synthetic_page() -> np.ndarray:
    image = np.full((1200, 900, 3), 35, dtype=np.uint8)
    page = np.array([[130, 90], [780, 150], [730, 1110], [90, 1050]], dtype=np.int32)
    cv2.fillConvexPoly(image, page, (245, 245, 245))
    cv2.polylines(image, [page], True, (220, 220, 220), 5)

    for y in range(250, 950, 75):
        cv2.line(image, (220, y), (650, y + 20), (20, 20, 20), 5)

    cv2.rectangle(image, (520, 780), (650, 900), (45, 45, 180), 8)
    return image


def test_order_points_returns_expected_order():
    pts = np.array([[500, 700], [100, 100], [520, 120], [80, 680]], dtype=np.float32)
    ordered = order_points(pts)
    assert np.allclose(ordered[0], [100, 100])
    assert np.allclose(ordered[1], [520, 120])
    assert np.allclose(ordered[2], [500, 700])
    assert np.allclose(ordered[3], [80, 680])


def test_detect_document_finds_synthetic_page():
    image = _synthetic_page()
    result = detect_document(image, min_confidence=0.60)

    assert result.corners is not None
    assert result.confidence >= 0.60
    assert result.needs_review is False


def test_detect_document_fails_safe_without_page():
    image = np.full((600, 800, 3), 128, dtype=np.uint8)
    result = detect_document(image)

    assert result.corners is None
    assert result.needs_review is True
    assert result.reason == "no-quadrilateral"


def test_perspective_rectify_produces_nonempty_page():
    image = _synthetic_page()
    corners = np.array([[130, 90], [780, 150], [730, 1110], [90, 1050]], dtype=np.float32)
    out = perspective_rectify(image, corners)

    assert out.shape[0] > 800
    assert out.shape[1] > 500
    assert out.size > 0


def test_rotate_expand_does_not_clip_canvas():
    image = np.full((300, 500, 3), 255, dtype=np.uint8)
    out = rotate_expand(image, 5.0)
    assert out.shape[0] > image.shape[0]
    assert out.shape[1] > image.shape[1]


def test_deskew_returns_image_and_numeric_angle():
    image = np.full((700, 900, 3), 255, dtype=np.uint8)
    for y in range(150, 550, 50):
        cv2.line(image, (120, y), (780, y), (0, 0, 0), 4)

    skewed = rotate_expand(image, 3.0)
    corrected, angle = deskew(skewed)

    assert corrected.size > 0
    assert isinstance(angle, float)
    assert abs(angle) <= 7.0
