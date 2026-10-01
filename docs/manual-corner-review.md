# Manual Corner Review

V0.4 introduces a lightweight review workflow for real photos where automatic page boundaries are uncertain.

## Why this exists

Real phone photos often include:
- stacked pages
- clipped page corners
- colored headers
- weak page/background separation
- perspective that cannot be trusted from one detector alone

In those cases ScanFix should propose corners, but the user decides the physical page boundary.

## Step 1 — generate the review page

```powershell
py tools/review_corners.py "input.jpg" "review.html"
```

Open `review.html` in a browser.

The image is embedded in the file, so the review page is standalone.

## Step 2 — drag the four handles

The handles represent:

```text
TL -------- TR
|            |
|            |
BL -------- BR
```

Move each handle to the physical document corner.

Available actions:
- Download `review.json`
- Reset suggested corners
- Use full image frame

## Step 3 — process the reviewed page

```powershell
py tools/scanfix_geometry.py "input.jpg" "corrected.png" --corners-file "review.json" --pdf "corrected.pdf"
```

The approved corner coordinates are then used for perspective rectification.

## Design boundary

The review page:
- does not OCR the document
- does not edit text
- does not redraw stamps/signatures
- does not enhance the source
- only records four page coordinates

This prototype exists to validate the interaction before building the final Electron desktop interface.
