#!/usr/bin/env python3
"""Generate a standalone manual-corner review page."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from scanfix.geometry import detect_document
from scanfix.review_html import generate_review_html


def main() -> int:
    ap = argparse.ArgumentParser(description="Create ScanFix manual corner review HTML.")
    ap.add_argument("input", type=Path)
    ap.add_argument("output_html", type=Path)
    ap.add_argument("--min-confidence", type=float, default=0.72)
    args = ap.parse_args()

    src = args.input.expanduser().resolve()
    out = args.output_html.expanduser().resolve()

    if not src.is_file():
        raise SystemExit(f"Input not found: {src}")

    image = cv2.imread(str(src), cv2.IMREAD_COLOR)
    if image is None:
        raise SystemExit("Could not decode input image.")

    detection = detect_document(image, min_confidence=args.min_confidence)

    generate_review_html(
        src,
        out,
        corners=detection.corners,
        confidence=detection.confidence,
        reason=detection.reason,
    )

    print("PASS")
    print(f"Reason: {detection.reason}")
    print(f"Confidence: {detection.confidence:.4f}")
    print(f"Review page: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
