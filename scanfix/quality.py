"""Lightweight image-quality signals for ScanFix V0.2."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class QualitySignals:
    blur_score: float
    brightness_mean: float
    contrast_std: float
    warnings: tuple[str, ...]


def analyze_quality(image: np.ndarray) -> QualitySignals:
    if image is None or image.size == 0:
        raise ValueError("empty image")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())

    warnings: list[str] = []
    if blur_score < 70:
        warnings.append("possible-blur")
    if brightness < 55:
        warnings.append("underexposed")
    elif brightness > 225:
        warnings.append("overexposed")
    if contrast < 28:
        warnings.append("low-contrast")

    return QualitySignals(
        blur_score=round(blur_score, 2),
        brightness_mean=round(brightness, 2),
        contrast_std=round(contrast, 2),
        warnings=tuple(warnings),
    )
