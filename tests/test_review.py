from pathlib import Path

import numpy as np
from PIL import Image

from scanfix.review import load_review_file
from scanfix.review_html import generate_review_html


def test_load_review_file(tmp_path: Path):
    path = tmp_path / "review.json"
    path.write_text(
        '{"accepted":true,"corners":[[10,10],[90,12],[88,120],[12,118]]}',
        encoding="utf-8",
    )

    corners = load_review_file(path)

    assert corners.shape == (4, 2)
    assert np.allclose(corners[0], [10, 10])


def test_reject_unaccepted_review(tmp_path: Path):
    path = tmp_path / "review.json"
    path.write_text(
        '{"accepted":false,"corners":[[10,10],[90,12],[88,120],[12,118]]}',
        encoding="utf-8",
    )

    try:
        load_review_file(path)
    except ValueError as exc:
        assert "not accepted" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_generate_review_html_embeds_image_and_corners(tmp_path: Path):
    image_path = tmp_path / "source.png"
    html_path = tmp_path / "review.html"
    Image.new("RGB", (200, 300), "white").save(image_path)

    corners = np.array(
        [[10, 10], [190, 12], [188, 290], [12, 288]],
        dtype=np.float32,
    )

    generate_review_html(
        image_path,
        html_path,
        corners=corners,
        confidence=0.66,
        reason="partial-page-or-cropped",
    )

    text = html_path.read_text(encoding="utf-8")
    assert "data:image/png;base64," in text
    assert "partial-page-or-cropped" in text
    assert "Download review.json" in text
