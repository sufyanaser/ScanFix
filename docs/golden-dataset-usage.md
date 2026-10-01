# Golden Dataset Usage

This milestone stays deliberately simple: create representative test cases, preserve the received pixels, and record what a safe correction should do.

## Install the small development dependencies

```powershell
py -m pip install -r requirements-dev.txt
```

## Add a real local document photo

Example:

```powershell
py tools/golden_ingest.py "C:\Users\SUFYAN\Pictures\book.jpg" --provenance whatsapp-photo --tags severe-perspective strong-shadow jpeg-compression colored-stamp --preserve-color --contains-stamp
```

This creates a local case:

```text
datasets/golden/samples/GD-001/
  source.jpg
  metadata.json
```

The source image is copied unchanged. The tool records its SHA-256 and basic dimensions. The local `samples/` content remains ignored by Git.

## Cases expected to require manual review

```powershell
py tools/golden_ingest.py "C:\path\difficult.jpg" --provenance phone-camera --tags partial-page occluded-edge weak-boundary --manual-review
```

## Review metadata

After adding a case, open its `metadata.json` and complete only what is known reliably:
- page corners
- orientation
- approximate deskew
- notes
- review status

Do not invent precise ground truth when an edge is genuinely ambiguous. Mark the case for manual review instead.

## Validate repository fixtures

```powershell
py tools/validate_golden.py
```

Validate repository fixtures plus your local cases:

```powershell
py tools/validate_golden.py --local
```

## What this validation is for

The validator checks:
- manifests match the schema
- case IDs are unique
- the bootstrap corpus exists
- content reconstruction remains forbidden
- local document samples are not accidentally tracked by Git

It does **not** attempt OCR, image enhancement, document classification, or any processing-engine work.
