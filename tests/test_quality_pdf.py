from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from scanfix.pdf_export import export_pdf
from scanfix.quality import analyze_quality


def test_quality_detects_low_contrast():
    image = np.full((400, 600, 3), 128, dtype=np.uint8)
    q = analyze_quality(image)
    assert "low-contrast" in q.warnings


def test_quality_detects_bright_image():
    image = np.full((400, 600, 3), 245, dtype=np.uint8)
    q = analyze_quality(image)
    assert "overexposed" in q.warnings


def test_pdf_export_source_size(tmp_path: Path):
    src = tmp_path / "page.png"
    pdf = tmp_path / "page.pdf"
    Image.new("RGB", (600, 900), "white").save(src)

    export_pdf(src, pdf, page_size="source")

    assert pdf.exists()
    assert pdf.stat().st_size > 0


def test_pdf_export_a4_canvas(tmp_path: Path):
    src = tmp_path / "page.png"
    pdf = tmp_path / "page-a4.pdf"
    Image.new("RGB", (800, 800), "white").save(src)

    export_pdf(src, pdf, page_size="a4")

    assert pdf.exists()
    assert pdf.stat().st_size > 0
