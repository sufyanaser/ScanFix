#!/usr/bin/env python3
"""Create a local Golden Dataset case without modifying the source document."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import shutil
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "datasets" / "golden" / "samples"

ALLOWED_TAGS = {
    "clean", "mild-perspective", "severe-perspective", "rotation", "deskew",
    "curved-page", "folded-page", "partial-page", "occluded-edge", "hand-visible",
    "weak-boundary", "white-on-white", "busy-background", "strong-shadow",
    "uneven-lighting", "underexposed", "overexposed", "motion-blur", "focus-blur",
    "jpeg-compression", "low-resolution", "colored-stamp", "faint-stamp",
    "signature", "handwriting", "table", "thin-lines", "carbon-copy",
    "mixed-arabic-latin", "eastern-arabic-digits",
}

PROVENANCE = {
    "phone-camera", "whatsapp-photo", "whatsapp-document",
    "scanner", "synthetic", "public-domain", "other",
}

MIME_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".heic": "image/heic",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def next_case_id() -> str:
    SAMPLES.mkdir(parents=True, exist_ok=True)
    used = []
    for p in SAMPLES.glob("GD-*"):
        if p.is_dir():
            try:
                used.append(int(p.name.split("-", 1)[1]))
            except (ValueError, IndexError):
                pass
    n = max([x for x in used if x < 900] or [0]) + 1
    return f"GD-{n:03d}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Add one local source image to the ScanFix Golden Dataset.")
    ap.add_argument("source", type=Path)
    ap.add_argument("--case-id", help="Optional explicit ID such as GD-001")
    ap.add_argument("--provenance", choices=sorted(PROVENANCE), default="phone-camera")
    ap.add_argument("--tags", nargs="+", required=True, help="Taxonomy tags")
    ap.add_argument("--notes", default="")
    ap.add_argument("--sensitive", action="store_true", help="Mark local metadata as sensitive")
    ap.add_argument("--preserve-color", action="store_true")
    ap.add_argument("--contains-stamp", action="store_true")
    ap.add_argument("--contains-signature", action="store_true")
    ap.add_argument("--manual-review", action="store_true",
                    help="Expected to require human review before safe auto-processing")
    args = ap.parse_args()

    src = args.source.expanduser().resolve()
    if not src.is_file():
        raise SystemExit(f"Source file not found: {src}")

    bad = sorted(set(args.tags) - ALLOWED_TAGS)
    if bad:
        raise SystemExit(f"Unknown taxonomy tags: {', '.join(bad)}")

    ext = src.suffix.lower()
    mime = MIME_MAP.get(ext) or mimetypes.guess_type(src.name)[0]
    if mime not in {"image/jpeg", "image/png", "image/heic", "image/tiff"}:
        raise SystemExit(f"Unsupported image type: {mime or ext}")

    # Pillow reads common formats directly. HEIC may require an installed decoder plugin.
    try:
        with Image.open(src) as im:
            width, height = im.size
    except Exception as exc:
        raise SystemExit(
            f"Could not read image dimensions: {exc}. "
            "For HEIC, convert a copy to JPEG/PNG or install a Pillow HEIC plugin."
        )

    case_id = args.case_id or next_case_id()
    if not case_id.startswith("GD-") or not case_id[3:].isdigit():
        raise SystemExit("case-id must look like GD-001")

    case_dir = SAMPLES / case_id
    if case_dir.exists():
        raise SystemExit(f"Case already exists: {case_dir}")

    case_dir.mkdir(parents=True)
    dst = case_dir / f"source{ext}"
    shutil.copy2(src, dst)

    manifest = {
        "case_id": case_id,
        "source": {
            "filename": dst.name,
            "sha256": sha256_file(dst),
            "mime_type": mime,
            "width_px": width,
            "height_px": height,
            "provenance": args.provenance,
            "sensitive": bool(args.sensitive),
            "notes": args.notes,
        },
        "taxonomy": args.tags,
        "ground_truth": {
            "page_corners_px": None,
            "orientation_deg": None,
            "deskew_deg": None,
            "reference_notes": "Complete after visual review.",
        },
        "expected": {
            "auto_process_allowed": not args.manual_review,
            "manual_review_allowed": True,
            "content_reconstruction_allowed": False,
            "must_preserve_color": bool(args.preserve_color),
            "must_preserve_stamp": bool(args.contains_stamp),
            "must_preserve_signature": bool(args.contains_signature),
            "expected_failure_mode": "manual-review" if args.manual_review else None,
        },
        "review": {
            "status": "unreviewed",
            "reviewer": "",
            "review_notes": "",
        },
    }

    (case_dir / "metadata.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Created {case_id}")
    print(f"Local source: {dst}")
    print(f"SHA-256: {manifest['source']['sha256']}")
    print("Next: review corners/orientation and update metadata.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
