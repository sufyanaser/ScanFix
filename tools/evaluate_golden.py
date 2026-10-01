#!/usr/bin/env python3
"""Evaluate ScanFix page detection against local Golden Dataset cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from scanfix.evaluation import evaluate_case
from scanfix.geometry import detect_document

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "datasets" / "golden" / "samples"
RESULTS = ROOT / "datasets" / "golden" / "results"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Evaluate local ScanFix Golden Dataset images.")
    ap.add_argument("--min-confidence", type=float, default=0.72)
    ap.add_argument("--corner-tolerance-pct", type=float, default=2.5)
    ap.add_argument("--output", type=Path, default=RESULTS / "latest-evaluation.json")
    args = ap.parse_args()

    rows = []

    for metadata_path in sorted(SAMPLES.glob("GD-*/metadata.json")):
        meta = load_json(metadata_path)
        case_dir = metadata_path.parent
        source_path = case_dir / meta["source"]["filename"]

        row = {
            "case_id": meta["case_id"],
            "source": str(source_path),
            "status": "not-run",
        }

        if not source_path.is_file():
            row["status"] = "missing-source"
            rows.append(row)
            continue

        image = cv2.imread(str(source_path), cv2.IMREAD_COLOR)
        if image is None:
            row["status"] = "decode-failed"
            rows.append(row)
            continue

        detection = detect_document(image, min_confidence=args.min_confidence)

        gt = meta.get("ground_truth", {})
        corners = gt.get("page_corners_px")
        expected_corners = (
            np.asarray(corners, dtype=np.float32)
            if corners is not None
            else None
        )

        ev = evaluate_case(
            detection,
            auto_process_allowed=bool(meta["expected"]["auto_process_allowed"]),
            expected_corners=expected_corners,
            image_width=image.shape[1],
            image_height=image.shape[0],
            corner_tolerance_pct=args.corner_tolerance_pct,
        )

        row.update(
            {
                "status": "evaluated",
                "expected_auto_process": bool(meta["expected"]["auto_process_allowed"]),
                "detected_needs_review": detection.needs_review,
                "detection_reason": detection.reason,
                "confidence": detection.confidence,
                "area_ratio": detection.area_ratio,
                "routing_pass": ev.routing_pass,
                "corner_error_pct": ev.corner_error_pct,
                "corner_pass": ev.corner_pass,
            }
        )
        rows.append(row)

    evaluated = [r for r in rows if r["status"] == "evaluated"]
    routing_passes = sum(1 for r in evaluated if r.get("routing_pass") is True)
    corner_rows = [r for r in evaluated if r.get("corner_pass") is not None]
    corner_passes = sum(1 for r in corner_rows if r.get("corner_pass") is True)

    summary = {
        "cases_found": len(rows),
        "evaluated": len(evaluated),
        "missing_or_failed": len(rows) - len(evaluated),
        "routing_pass": routing_passes,
        "routing_rate_pct": (
            round(routing_passes / len(evaluated) * 100.0, 2)
            if evaluated
            else None
        ),
        "corner_cases_measured": len(corner_rows),
        "corner_pass": corner_passes,
        "corner_rate_pct": (
            round(corner_passes / len(corner_rows) * 100.0, 2)
            if corner_rows
            else None
        ),
        "min_confidence": args.min_confidence,
        "corner_tolerance_pct": args.corner_tolerance_pct,
    }

    payload = {"summary": summary, "cases": rows}

    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Report: {output}")

    # Missing local samples are not a code failure. Failed evaluated routing/corners are.
    failed = any(
        r["status"] == "evaluated"
        and (
            r.get("routing_pass") is False
            or r.get("corner_pass") is False
        )
        for r in rows
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
