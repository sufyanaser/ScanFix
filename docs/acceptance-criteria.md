# ScanFix Acceptance Criteria

These criteria govern the first geometry/preservation milestone. They intentionally prioritize documentary integrity over visual attractiveness.

## Non-negotiable invariant

**Silent destructive failure = 0.**

If ScanFix is uncertain, it must stop, warn, or request human review. It must not silently invent, erase, reconstruct, or materially alter documentary content.

## A. Source preservation

| ID | Criterion | Required |
|---|---|---:|
| SRC-01 | Input source remains byte-for-byte unchanged after processing | 100% |
| SRC-02 | SHA-256 recorded before processing and re-checkable later | 100% |
| SRC-03 | Source and derivative are stored as distinct artifacts | 100% |
| SRC-04 | Processing never overwrites the source path | 100% |

Any failure in SRC-01..04 is release-blocking.

## B. Geometry

### Boundary detection
- Easy/clean cases: >= 98% correct auto-detection.
- Entire approved corpus: >= 95% either correctly auto-detected OR correctly routed to manual review.
- False confident crop that removes documentary content: 0 cases.

### Orientation
- Correct 0/90/180/270 orientation on >= 99% of applicable cases.
- Uncertain cases must be flagged rather than guessed.

### Deskew
- For cases with measurable skew, residual skew target <= 0.5 degrees after automatic correction.
- If confidence is below the configured threshold, correction must not be applied silently.

### Perspective rectification
- No visible clipping of intended page content.
- Corner reprojection must remain within the configured tolerance against human-reviewed corners.
- Initial target: median corner error <= 1.0% of image diagonal on cases with reliable ground truth.
- 95th percentile corner error <= 2.5% of image diagonal.
- Ambiguous/occluded cases are expected to route to manual review.

## C. Content integrity

Protected content includes text, numerals, stamps, signatures, handwritten notes, table borders, and faint marks.

Required:
- Generative reconstruction: prohibited.
- Content-aware fill inside the document: prohibited.
- AI text rewriting/correction in the image layer: prohibited.
- Automatic removal of stamps/signatures/handwriting: prohibited.
- Any processing path that can materially change protected content must be opt-in and visibly labelled as non-preservation output.

Release gate:
- 0 known cases of undetected removal, substitution, or invention of protected content in the Golden Dataset.

## D. Visual processing

For the preservation derivative:
- no aggressive thresholding by default
- no forced grayscale when color is semantically meaningful
- no sharpening that creates obvious halos or false strokes
- no background normalization that erases faint ink
- no upscaling claim that implies recovered source detail

Color-sensitive cases must preserve distinguishability of colored stamps/marks.

## E. Manual review behavior

At least 20% of the initial Golden Dataset should intentionally contain cases where auto-processing is unsafe.

For those cases:
- >= 95% must be correctly stopped/flagged for review.
- A manual four-corner editor must permit correction without modifying the source.
- Reset must restore the unprocessed derivative state.
- The UI must expose what operations will be applied before export.

## F. Export

For each supported export:
- output opens successfully in at least two independent viewers
- page is not unintentionally cropped
- orientation is correct
- aspect ratio is preserved unless the user explicitly requests normalization
- source-resolution limitations are not misrepresented as native 300 DPI detail

For PDF:
- page dimensions must match the chosen export mode
- image content must remain visually inspectable without OCR
- OCR, when later introduced, must be a separate searchable layer and never replace the image layer

## G. Determinism

For deterministic processing profiles:
- identical source + identical engine version + identical configuration must produce identical operation parameters
- output pixel hash should be stable where codec/library determinism permits it
- if binary output is not deterministic, the normalized processing record must be deterministic

## H. Audit trail

Every processed case must record:
- case ID
- source SHA-256
- engine version
- operation list
- operation parameters
- confidence values
- output SHA-256
- warnings
- whether manual intervention occurred
- timestamp

## I. Reliability

Initial release-candidate targets:
- successful processing/export without application crash: >= 99% of supported cases
- unsupported or corrupted input handled with explicit error: 100%
- no source-file corruption: 100%
- no silent destructive failure: 100%

## J. Release decision

A release candidate FAILS if any of the following occur:
1. source file changes
2. documentary content is silently clipped, erased, invented, or substituted
3. unsafe geometry is applied with high confidence instead of requesting review
4. an export is labelled archival/compliant without validation
5. the application claims resolution/detail that did not exist in the source

A release candidate may pass only when all release-blocking invariants pass and quantitative geometry/reliability thresholds meet this document.
