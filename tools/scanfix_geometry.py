#!/usr/bin/env python3
"""ScanFix Geometry V0.2 CLI.

Safe default:
- auto-detect page
- stop on low confidence
- rectify perspective
- optionally deskew
- report basic quality warnings
- optionally export PDF from the corrected raster image

No OCR. No generative processing. No content reconstruction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from scanfix.geometry import detect_document, deskew, order_points, perspective_rectify
from scanfix.pdf_export import export_pdf
from scanfix.quality import analyze_quality


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_corners(raw: str) -> np.ndarray:
    parts = raw.replace(";", " ").split()
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            'corners must contain four points, e.g. "100,80 1500,120 1480,2100 90,2080"'
        )

    pts = []
    for item in parts:
        try:
            x, y = item.split(",", 1)
            pts.append((float(x), float(y)))
        except Exception as exc:
            raise argparse.ArgumentTypeError(f"invalid point: {item}") from exc

    return order_points(pts)


def main() -> int:
    ap = argparse.ArgumentParser(description="Conservative document geometry correction.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, help="Output PNG/JPEG/TIFF path")
    ap.add_argument("--corners", type=parse_corners, help="Manual corners: TL/TR/BR/BL coordinates")
    ap.add_argument("--min-confidence", type=float, default=0.72)
    ap.add_argument("--no-deskew", action="store_true")
    ap.add_argument("--report", type=Path, help="Optional JSON report path")
    ap.add_argument("--pdf", type=Path, help="Optional PDF output path")
    ap.add_argument("--pdf-page", choices=["source", "a4"], default="source")
    args = ap.parse_args()

    src = args.input.expanduser().resolve()
    out = args.output.expanduser().resolve()
    report_path = (
        args.report.expanduser().resolve()
        if args.report
        else out.with_suffix(out.suffix + ".json")
    )
    pdf_path = args.pdf.expanduser().resolve() if args.pdf else None

    if not src.is_file():
        raise SystemExit(f"Input not found: {src}")
    if src == out:
        raise SystemExit("Output must not overwrite the source file.")
    if pdf_path is not None and pdf_path == src:
        raise SystemExit("PDF output must not overwrite the source file.")

    image = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit("Could not decode input image.")

    quality = analyze_quality(image)

    manual = args.corners is not None
    area_ratio = 0.0

    if manual:
        corners = args.corners
        confidence = 1.0
        detection_reason = "manual-corners"
        needs_review = False
    else:
        detection = detect_document(image, min_confidence=args.min_confidence)
        corners = detection.corners
        confidence = detection.confidence
        detection_reason = detection.reason
        needs_review = detection.needs_review
        area_ratio = detection.area_ratio

        if corners is None or needs_review:
            report = {
                "status": "needs-review",
                "source": str(src),
                "source_sha256": sha256_file(src),
                "quality": {
                    "blur_score": quality.blur_score,
                    "brightness_mean": quality.brightness_mean,
                    "contrast_std": quality.contrast_std,
                    "warnings": list(quality.warnings),
                },
                "page_detection": {
                    "confidence": confidence,
                    "reason": detection_reason,
                    "area_ratio": area_ratio,
                    "corners": corners.tolist() if corners is not None else None,
                },
                "operations_applied": [],
            }

            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

            print("NEEDS_REVIEW")
            print(f"Reason: {detection_reason}")
            print(f"Confidence: {confidence:.4f}")
            if quality.warnings:
                print("Quality warnings: " + ", ".join(quality.warnings))
            print(f"Report: {report_path}")
            return 2

    rectified = perspective_rectify(image, corners)
    applied = ["perspective-rectify"]

    skew_angle = 0.0
    result = rectified

    if not args.no_deskew:
        result, skew_angle = deskew(rectified)
        if skew_angle:
            applied.append("deskew")

    out.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(out), result):
        raise SystemExit(f"Failed to write output: {out}")

    if pdf_path is not None:
        export_pdf(out, pdf_path, page_size=args.pdf_page)
        applied.append("pdf-export")

    report = {
        "status": "ok",
        "source": str(src),
        "source_sha256": sha256_file(src),
        "output": str(out),
        "output_sha256": sha256_file(out),
        "manual_corners": manual,
        "quality": {
            "blur_score": quality.blur_score,
            "brightness_mean": quality.brightness_mean,
            "contrast_std": quality.contrast_std,
            "warnings": list(quality.warnings),
        },
        "page_detection": {
            "confidence": confidence,
            "reason": detection_reason,
            "area_ratio": area_ratio,
            "corners": np.asarray(corners).round(3).tolist(),
        },
        "deskew": {
            "enabled": not args.no_deskew,
            "detected_angle_deg": skew_angle,
        },
        "operations_applied": applied,
        "output_size_px": [int(result.shape[1]), int(result.shape[0])],
        "pdf": (
            {
                "path": str(pdf_path),
                "sha256": sha256_file(pdf_path),
                "page_mode": args.pdf_page,
            }
            if pdf_path is not None
            else None
        ),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PASS")
    print(f"Output: {out}")
    if pdf_path is not None:
        print(f"PDF: {pdf_path}")
    if quality.warnings:
        print("Quality warnings: " + ", ".join(quality.warnings))
    print(f"Report: {report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
