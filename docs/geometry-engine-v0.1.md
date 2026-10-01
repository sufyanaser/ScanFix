# Geometry Engine V0.1

This is the first real processing milestone for ScanFix.

## Scope

Implemented:
- automatic document quadrilateral detection
- detection confidence + safe review gate
- manual four-corner input
- perspective rectification
- residual deskew estimation
- rotation with expanded canvas to avoid clipping
- output image
- JSON processing report with source/output SHA-256

Not implemented:
- OCR
- text reconstruction
- generative enhancement
- ML dewarping
- shadow removal
- color enhancement
- PDF/PDF-A
- batch processing
- GUI

## CLI

Install:

```powershell
py -m pip install -r requirements-engine.txt
```

Automatic:

```powershell
py tools/scanfix_geometry.py input.jpg output.png
```

If confidence is insufficient, the CLI exits with code `2`, writes a report, and does not create a corrected image.

Manual corners:

```powershell
py tools/scanfix_geometry.py input.jpg output.png --corners "120,90 1820,140 1780,2480 80,2420"
```

Disable deskew:

```powershell
py tools/scanfix_geometry.py input.jpg output.png --no-deskew
```

## Design rule

V0.1 may move existing pixels geometrically. It may not generate, rewrite, erase, or reconstruct documentary content.

Automatic geometry is deliberately conservative. When page detection is ambiguous, the intended behavior is a review request rather than a forced correction.

## Exit codes

- `0`: corrected image written successfully
- `2`: safe stop; manual review/corners required
- other non-zero: invalid input or processing failure

## Validation

```powershell
py -m pytest -q
```

The unit tests use synthetic geometric pages only. Real document acceptance remains governed by the Golden Dataset.
