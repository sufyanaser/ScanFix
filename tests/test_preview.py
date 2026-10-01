import numpy as np

from scanfix.preview import draw_detection_preview


def test_preview_preserves_shape_and_draws():
    image = np.full((600, 800, 3), 255, dtype=np.uint8)
    corners = np.array(
        [[100, 80], [700, 90], [690, 520], [110, 510]],
        dtype=np.float32,
    )

    preview = draw_detection_preview(
        image,
        corners,
        confidence=0.91,
        reason="ok",
    )

    assert preview.shape == image.shape
    assert not np.array_equal(preview, image)


def test_preview_handles_missing_corners():
    image = np.full((400, 600, 3), 255, dtype=np.uint8)

    preview = draw_detection_preview(
        image,
        None,
        confidence=0.0,
        reason="no-quadrilateral",
    )

    assert preview.shape == image.shape
    assert not np.array_equal(preview, image)
