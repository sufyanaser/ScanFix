# ScanFix

ScanFix is a Windows-focused document rectification utility for safely converting phone/WhatsApp document photos into human-verifiable, print-ready digital documents without generative reconstruction.

## Development model

`develop` is the development source of truth.

The project now includes the **Golden Dataset baseline** and **Geometry Engine V0.3**. The engine provides conservative multi-pass page detection, brightness-segmentation fallback for real phone photos, confidence gating, cropped/stacked-page review routing, manual-corner fallback, perspective rectification, deskew, basic quality warnings, preview overlays, raster PDF export, local Golden Dataset evaluation, unit tests, and CI validation. OCR and generative processing remain out of scope.

## Baseline documents

- [Acceptance criteria](docs/acceptance-criteria.md)
- [Validation plan](docs/validation-plan.md)
- [Golden Dataset collection protocol](docs/dataset-collection-protocol.md)
- [Test taxonomy](docs/test-taxonomy.md)
- [Golden Dataset schema](datasets/golden/manifest.schema.json)
- [Example manifest](datasets/golden/manifest.example.json)
- [Golden Dataset usage](docs/golden-dataset-usage.md)
- [Geometry Engine V0.1](docs/geometry-engine-v0.1.md)
- [Geometry Engine V0.2](docs/geometry-engine-v0.2.md)
- [First real sample evaluation](docs/real-sample-evaluation.md)

## Safety principle

**Silent destructive failure = 0.**

If ScanFix is uncertain, it must stop, warn, or request human review rather than silently clip, erase, invent, reconstruct, or substitute documentary content.

## Dataset privacy

Real administrative documents, IDs, signatures, stamps, and private WhatsApp media are ignored by Git by default. Public repository samples should be synthetic, public-domain, or explicitly de-identified and approved for publication.

## Current engine milestone

Geometry Engine V0.3 implements:

1. source SHA-256 reporting
2. page-boundary detection with confidence gating
3. manual four-corner fallback
4. perspective rectification
5. residual deskew
6. safe review routing when auto-detection is uncertain
7. quality warnings without altering the document
8. preview overlays for detected corners
9. optional PDF export
10. local Golden Dataset evaluation
11. segmentation fallback for weak/fragmented page edges
12. explicit `full-frame-document`, `partial-page-or-cropped`, and `stacked-pages-ambiguous` routing
13. unit tests and GitHub Actions validation

Next: run V0.2 against real local Golden Dataset images and tune thresholds from evidence. OCR, ML dewarping, batch processing, and generative enhancement remain out of scope.
