# Real Sample Evaluation — First Field Set

Four real-world document photos were used to challenge Geometry Engine V0.2 before adding more features.

## V0.2 result

V0.2 did not correctly identify the physical page boundary on any of the four samples. It selected small internal quadrilaterals instead.

This was a useful failure: the edge-only detector was too dependent on strong closed contours and ideal page/background separation.

## Observed field cases

### Case A — stacked official letter
Characteristics:
- front page over another sheet
- near-full-frame page
- repeated horizontal elements near the lower edge
- slight perspective
- stamps/signature/color

Expected routing:
- manual review

Reason:
A full-frame brightness mask can include the sheet underneath. Automatic cropping would risk selecting the wrong physical page boundary.

### Case B — photographed printed instruction sheet
Characteristics:
- strong white/dark background separation
- page partially clipped by image borders
- visible perspective
- text-heavy page

Expected routing:
- manual review / corner confirmation

Reason:
Several physical page corners extend to or beyond the captured frame. A quadrilateral can be proposed, but it should not be trusted silently.

### Case C — near scan-like bank letter
Characteristics:
- page fills nearly the entire frame
- little external background
- degraded/printed copy quality
- no useful outer page contour

Expected routing:
- automatic full-frame document
- preserve the full frame
- deskew only if supported by evidence

### Case D — colored lease contract
Characteristics:
- colored header
- page fills most of frame
- several edges touch/cross the captured frame
- substantial handwriting/stamps/signatures
- internal color transition can look like a false page edge

Expected routing:
- manual review / corner confirmation

Reason:
Brightness segmentation may mistake the colored header/body boundary for the physical top edge.

## V0.3 response

The detector now has two stages:

1. edge-based quadrilateral detection
2. brightness-segmentation fallback when edge detection is weak

The fallback distinguishes:
- `full-frame-document`
- `partial-page-or-cropped`
- `stacked-pages-ambiguous`
- `segmentation-page`

Only clear or full-frame single-page cases may continue automatically. Cropped/stacked/ambiguous cases retain proposed corners but are routed to manual review.

This improves usefulness without allowing aggressive automatic correction of uncertain documents.
