# Geometry Engine V0.2

V0.2 keeps the engine deterministic and conservative while making it more useful for real phone/WhatsApp document photos.

## Added in V0.2

- multi-pass Canny edge detection
- CLAHE-assisted weak-boundary pass
- multiple polygon approximation tolerances
- mild full-frame contour penalty
- page-area reporting
- lightweight quality signals:
  - blur score
  - mean brightness
  - contrast
- non-destructive quality warnings
- optional raster PDF export
- optional A4 export canvas

## Important behavior

Quality warnings do **not** alter the image. They are informational only.

The engine still performs only geometric correction:

```text
source
  -> detect page
  -> confidence gate
  -> perspective rectify
  -> optional deskew
  -> corrected raster
  -> optional PDF
```

## Automatic correction

```powershell
py tools/scanfix_geometry.py input.jpg corrected.png
```

## Correct image + PDF

```powershell
py tools/scanfix_geometry.py input.jpg corrected.png --pdf corrected.pdf
```

## A4 print-layout PDF

```powershell
py tools/scanfix_geometry.py input.jpg corrected.png --pdf corrected-a4.pdf --pdf-page a4
```

A4 mode only centers the corrected raster on an A4-ratio canvas. It does not claim that the original capture has 300 DPI or recovered detail.

## Manual corners

```powershell
py tools/scanfix_geometry.py input.jpg corrected.png --corners "120,90 1820,140 1780,2480 80,2420" --pdf corrected.pdf
```

## Quality warnings

Possible warnings:

- `possible-blur`
- `underexposed`
- `overexposed`
- `low-contrast`

Warnings are recorded in the JSON report and printed to the console.

## Still deliberately out of scope

- OCR
- generative enhancement
- ML dewarping
- automatic shadow removal
- automatic background whitening
- batch mode
- desktop GUI

The next validation target is a small set of real user document photos, especially WhatsApp-compressed pages and angled phone captures.
