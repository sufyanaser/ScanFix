"""Visual preview helpers for ScanFix detection review."""

from __future__ import annotations

import cv2
import numpy as np

from scanfix.geometry import order_points


def draw_detection_preview(
    image: np.ndarray,
    corners: np.ndarray | None,
    *,
    confidence: float,
    reason: str,
) -> np.ndarray:
    """Draw detected page corners and status on a copy of the source image."""
    canvas = image.copy()

    if corners is not None:
        pts = order_points(corners).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts], True, (0, 220, 0), 4)

        labels = ("TL", "TR", "BR", "BL")
        ordered = order_points(corners).astype(np.int32)
        for label, (x, y) in zip(labels, ordered):
            cv2.circle(canvas, (int(x), int(y)), 10, (0, 0, 255), -1)
            cv2.putText(
                canvas,
                label,
                (int(x) + 12, int(y) - 12),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

    status = f"confidence={confidence:.3f}  {reason}"
    cv2.rectangle(canvas, (12, 12), (min(canvas.shape[1] - 12, 640), 60), (0, 0, 0), -1)
    cv2.putText(
        canvas,
        status,
        (24, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    return canvas
