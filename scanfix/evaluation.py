"""Golden Dataset evaluation helpers for ScanFix."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from scanfix.geometry import DetectionResult, order_points


@dataclass(frozen=True)
class CaseEvaluation:
    routing_pass: bool
    corner_error_pct: float | None
    corner_pass: bool | None


def normalized_corner_error(
    detected: np.ndarray,
    expected: np.ndarray,
    image_width: int,
    image_height: int,
) -> float:
    """Mean corner distance as percentage of the image diagonal."""
    det = order_points(detected)
    exp = order_points(expected)

    distances = np.linalg.norm(det - exp, axis=1)
    diagonal = max(float(np.hypot(image_width, image_height)), 1.0)
    return round(float(distances.mean() / diagonal * 100.0), 4)


def evaluate_case(
    detection: DetectionResult,
    *,
    auto_process_allowed: bool,
    expected_corners: np.ndarray | None,
    image_width: int,
    image_height: int,
    corner_tolerance_pct: float = 2.5,
) -> CaseEvaluation:
    """Evaluate routing and optional corner accuracy for one Golden Dataset case."""
    routed_to_review = detection.needs_review or detection.corners is None

    if auto_process_allowed:
        routing_pass = not routed_to_review
    else:
        routing_pass = routed_to_review

    corner_error = None
    corner_pass = None

    if expected_corners is not None and detection.corners is not None:
        corner_error = normalized_corner_error(
            detection.corners,
            expected_corners,
            image_width,
            image_height,
        )
        corner_pass = corner_error <= corner_tolerance_pct

    return CaseEvaluation(
        routing_pass=routing_pass,
        corner_error_pct=corner_error,
        corner_pass=corner_pass,
    )
