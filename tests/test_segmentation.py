import cv2
import numpy as np

from scanfix.segmentation import detect_bright_page_candidate


def test_segmentation_detects_clear_page_on_dark_background():
    image = np.full((1200, 900, 3), 30, dtype=np.uint8)
    page = np.array(
        [[110, 90], [790, 130], [760, 1110], [80, 1060]],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(image, page, (240, 240, 240))

    result = detect_bright_page_candidate(image)

    assert result.corners is not None
    assert result.needs_review is False
    assert result.area_ratio > 0.5


def test_segmentation_marks_partial_page_for_review():
    image = np.full((1000, 700, 3), 25, dtype=np.uint8)
    page = np.array(
        [[0, 120], [699, 140], [699, 900], [0, 880]],
        dtype=np.int32,
    )
    cv2.fillConvexPoly(image, page, (245, 245, 245))

    result = detect_bright_page_candidate(image)

    assert result.corners is not None
    assert result.needs_review is True
    assert result.reason == "partial-page-or-cropped"


def test_segmentation_accepts_single_full_frame_document():
    image = np.full((900, 700, 3), 235, dtype=np.uint8)
    cv2.line(image, (80, 200), (620, 200), (20, 20, 20), 3)

    result = detect_bright_page_candidate(image)

    assert result.corners is not None
    assert result.reason == "full-frame-document"
