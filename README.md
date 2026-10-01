# ScanFix

ScanFix is a Windows-focused document rectification utility for safely converting phone/WhatsApp document photos into human-verifiable, print-ready digital documents without generative reconstruction.

## Development model

`develop` is the development source of truth.

The current milestone is the **Golden Dataset + Acceptance Criteria baseline**. It now includes 12 manifest-only bootstrap fixtures, a local ingest CLI, schema validation, and CI validation. No image-processing engine or OCR is included yet.

## Baseline documents

- [Acceptance criteria](docs/acceptance-criteria.md)
- [Validation plan](docs/validation-plan.md)
- [Golden Dataset collection protocol](docs/dataset-collection-protocol.md)
- [Test taxonomy](docs/test-taxonomy.md)
- [Golden Dataset schema](datasets/golden/manifest.schema.json)
- [Example manifest](datasets/golden/manifest.example.json)
- [Golden Dataset usage](docs/golden-dataset-usage.md)

## Safety principle

**Silent destructive failure = 0.**

If ScanFix is uncertain, it must stop, warn, or request human review rather than silently clip, erase, invent, reconstruct, or substitute documentary content.

## Dataset privacy

Real administrative documents, IDs, signatures, stamps, and private WhatsApp media are ignored by Git by default. Public repository samples should be synthetic, public-domain, or explicitly de-identified and approved for publication.

## Next engineering milestone

Build a minimal deterministic geometry engine and CLI for:

1. source preservation + SHA-256
2. page-boundary detection
3. orientation
4. four-corner perspective correction
5. deskew
6. manual-review routing

OCR, ML dewarping, PDF/A, batch processing, and generative enhancement remain out of scope until the geometry engine passes the Golden Dataset gates.
