# Validation Plan

## Purpose

Provide a repeatable test procedure for every ScanFix geometry-engine milestone.

## Test sets

Maintain three logical sets:
- **development**: used while tuning algorithms
- **validation**: used for routine release-candidate checks
- **holdout**: at least 20% of approved cases; not used for threshold tuning

## Per-case execution

For every case:

1. verify source SHA-256
2. load source without modifying it
3. run quality/boundary/orientation analysis
4. record confidence values
5. apply only operations allowed by the current milestone
6. export derivative
7. calculate output SHA-256
8. compare geometry against ground truth where available
9. inspect protected-content regions
10. classify result:
   - PASS
   - PASS_WITH_REVIEW
   - FAIL_SAFE
   - FAIL_DESTRUCTIVE

`FAIL_DESTRUCTIVE` is always release-blocking.

## Core metrics

### Boundary/corner metrics
- normalized corner error (% image diagonal)
- page-content clipping occurrence
- auto vs manual-review routing accuracy

### Orientation/deskew metrics
- orientation accuracy
- residual skew in degrees

### Preservation metrics
- source hash unchanged
- protected-region change review
- unexpected crop count
- destructive-failure count

### Reliability metrics
- crash count
- unsupported-input handling
- export-open success
- processing duration (informational in early milestones)

## Human visual review

Automated pixel-difference alone is insufficient after perspective transforms.

Human review must inspect:
- Arabic dots and diacritics
- Eastern Arabic numerals
- faint characters
- signatures
- colored/faint stamps
- thin table rules
- handwriting
- document edges

Use side-by-side and overlay/difference views when available.

## Baseline rule

The first engine implementation must be compared against a no-op baseline.

A new algorithm is not accepted merely because output looks cleaner. It must improve geometry or usability without increasing destructive failure risk.

## Regression rule

Once a case passes a release milestone, any later failure on that case is a regression unless:
- the test case itself was corrected, and
- the correction is documented in version control.

## Reporting

Each validation run should emit a machine-readable summary and a human-readable report containing:
- engine/version
- dataset manifest version
- total cases
- passes
- safe failures
- destructive failures
- manual-review cases
- metric aggregates
- changed results since previous baseline

No release should be tagged from a run containing a destructive failure.
