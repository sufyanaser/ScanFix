"""Manual corner-review data model for ScanFix."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scanfix.geometry import order_points


def load_review_file(path: Path) -> np.ndarray:
    """Load four approved corners from a ScanFix review JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    if data.get("accepted") is not True:
        raise ValueError("review file is not accepted")

    corners = data.get("corners")
    if not isinstance(corners, list) or len(corners) != 4:
        raise ValueError("review file must contain exactly four corners")

    pts = np.asarray(corners, dtype=np.float32)
    if pts.shape != (4, 2):
        raise ValueError("corners must be four [x, y] pairs")

    if not np.isfinite(pts).all():
        raise ValueError("corner coordinates must be finite")

    return order_points(pts)
