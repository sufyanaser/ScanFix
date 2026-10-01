import numpy as np

from scanfix.evaluation import evaluate_case, normalized_corner_error
from scanfix.geometry import DetectionResult


def test_normalized_corner_error_zero_for_identical_corners():
    corners = np.array(
        [[100, 100], [900, 100], [900, 1300], [100, 1300]],
        dtype=np.float32,
    )
    err = normalized_corner_error(corners, corners, 1000, 1400)
    assert err == 0.0


def test_evaluate_case_passes_expected_auto_route():
    corners = np.array(
        [[100, 100], [900, 100], [900, 1300], [100, 1300]],
        dtype=np.float32,
    )
    detection = DetectionResult(
        corners=corners,
        confidence=0.9,
        needs_review=False,
        reason="ok",
        area_ratio=0.7,
    )

    result = evaluate_case(
        detection,
        auto_process_allowed=True,
        expected_corners=corners,
        image_width=1000,
        image_height=1400,
    )

    assert result.routing_pass is True
    assert result.corner_pass is True


def test_evaluate_case_passes_expected_manual_review_route():
    detection = DetectionResult(
        corners=None,
        confidence=0.0,
        needs_review=True,
        reason="no-quadrilateral",
        area_ratio=0.0,
    )

    result = evaluate_case(
        detection,
        auto_process_allowed=False,
        expected_corners=None,
        image_width=1000,
        image_height=1400,
    )

    assert result.routing_pass is True
    assert result.corner_pass is None
