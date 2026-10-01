import cv2
import numpy as np

from scanfix.geometry import detect_document


def test_full_frame_document_fallback_is_accepted():
    image = np.full((1200, 900, 3), 238, dtype=np.uint8)
    for y in range(220, 900, 70):
        cv2.line(image, (140, y), (760, y), (25, 25, 25), 3)

    result = detect_document(image)

    assert result.corners is not None
    assert result.needs_review is False
    assert result.reason in {"full-frame-document", "ok"}


def test_cropped_page_is_not_silently_accepted():
    image = np.full((1200, 900, 3), 30, dtype=np.uint8)
    page = np.array(
        [[0, 150], [899, 180], [899, 1100], [0, 1060]],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(image, page, (240, 240, 240))
    for y in range(300, 900, 70):
        cv2.line(image, (100, y), (780, y), (20, 20, 20), 3)

    result = detect_document(image)

    assert result.corners is not None
    assert result.needs_review is True
    assert result.reason in {
        "partial-page-or-cropped",
        "low-confidence",
        "page-too-small-or-ambiguous",
    }
