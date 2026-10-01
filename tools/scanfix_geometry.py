#!/usr/bin/env python3
"""ScanFix Geometry V0.1 CLI.

Safe default:
- auto-detect page
- stop on low confidence
- rectify perspective
- optionally deskew
- export PNG + JSON report

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
    ap = argparse.ArgumentParser(description="Safe document geometry correction.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, help="Output PNG/JPEG/TIFF path")
    ap.add_argument("--corners", type=parse_corners, help="Manual corners: TL/TR/BR/BL coordinates")
    ap.add_argument("--min-confidence", type=float, default=0.72)
    ap.add_argument("--no-deskew", action="store_true")
    ap.add_argument("--report", type=Path, help="Optional JSON report path")
    args = ap.parse_args()

    src = args.input.expanduser().resolve()
    out = args.output.expanduser().resolve()
    report_path = args.report.expanduser().resolve() if args.report else out.with_suffix(out.suffix + ".json")

    if not src.is_file():
        raise SystemExit(f"Input not found: {src}")
    if src == out:
        raise SystemExit("Output must not overwrite the source file.")

    image = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit("Could not decode input image.")

    manual = args.corners is not None
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

        if corners is None or needs_review:
            report = {
                "status": "needs-review",
                "source": str(src),
                "source_sha256": sha256_file(src),
                "page_detection": {
                    "confidence": confidence,
                    "reason": detection_reason,
                    "corners": corners.tolist() if corners is not None else None,
                },
                "operations_applied": [],
            }
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print("NEEDS_REVIEW")
            print(f"Reason: {detection_reason}")
            print(f"Confidence: {confidence:.4f}")
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

    report = {
        "status": "ok",
        "source": str(src),
        "source_sha256": sha256_file(src),
        "output": str(out),
        "output_sha256": sha256_file(out),
        "manual_corners": manual,
        "page_detection": {
            "confidence": confidence,
            "reason": detection_reason,
            "corners": np.asarray(corners).round(3).tolist(),
        },
        "deskew": {
            "enabled": not args.no_deskew,
            "detected_angle_deg": skew_angle,
        },
        "operations_applied": applied,
        "output_size_px": [int(result.shape[1]), int(result.shape[0])],
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("PASS")
    print(f"Output: {out}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
