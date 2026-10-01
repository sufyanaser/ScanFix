"""Simple raster PDF export for ScanFix.

This preserves the processed page as an image inside a PDF.
No OCR/text reconstruction is performed.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def export_pdf(image_path: Path, pdf_path: Path, page_size: str = "source") -> None:
    image_path = Path(image_path)
    pdf_path = Path(pdf_path)

    with Image.open(image_path) as im:
        rgb = im.convert("RGB")

        if page_size == "a4":
            # A4 aspect ratio canvas. This is an export layout only; it does not claim 300 DPI.
            a4_ratio = 210 / 297
            src_ratio = rgb.width / rgb.height

            if src_ratio > a4_ratio:
                canvas_w = rgb.width
                canvas_h = round(canvas_w / a4_ratio)
            else:
                canvas_h = rgb.height
                canvas_w = round(canvas_h * a4_ratio)

            canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
            x = (canvas_w - rgb.width) // 2
            y = (canvas_h - rgb.height) // 2
            canvas.paste(rgb, (x, y))
            rgb = canvas
        elif page_size != "source":
            raise ValueError("page_size must be 'source' or 'a4'")

        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        rgb.save(pdf_path, "PDF", resolution=150.0)
