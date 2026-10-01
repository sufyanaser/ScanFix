# Golden Dataset Collection Protocol

## Objective

Build a representative, reviewable corpus for ScanFix before implementing the document-processing engine.

The corpus exists to answer one question:

> Can ScanFix correct document geometry and produce usable derivatives without silently altering documentary content?

## 1. Source acquisition

Preferred sources:
- phone-camera photos captured under realistic office conditions
- WhatsApp-compressed document photos
- photos with perspective distortion, shadows, clutter, weak edges, stamps, signatures, handwritten notes, tables, and mixed Arabic/Latin text
- synthetic/public-domain samples for repository-safe examples

Do not upload confidential administrative documents to the public GitHub repository.

## 2. Preserve the source

For every case:
1. Copy the received file into a new local case directory.
2. Do not overwrite, rotate, crop, recompress, resize, rename destructively, or modify metadata on the source.
3. Calculate SHA-256 before any processing.
4. Record MIME type, dimensions, provenance, and sensitivity.
5. Treat the source file as immutable evidence of what ScanFix received.

## 3. Case IDs

Use stable IDs:

```
GD-001
GD-002
GD-003
```

Never reuse an ID for another source.

## 4. Ground truth

Where geometry is measurable, two human reviews should establish:
- page corners
- expected orientation
- approximate deskew angle
- whether auto-processing is safe
- whether manual review is expected

Ground truth is not required to pretend certainty. If a corner is ambiguous, record that ambiguity and classify the case as requiring manual review.

## 5. Classification

Apply every relevant tag from `docs/test-taxonomy.md`.

Avoid single-label simplification. A real case may simultaneously be:
- severe-perspective
- strong-shadow
- jpeg-compression
- colored-stamp
- handwriting

## 6. Content-integrity annotation

Explicitly mark whether the source contains:
- stamps
- signatures
- handwriting
- faint text
- thin table lines
- carbon-copy text
- colored marks that must remain visually distinguishable

These become protected regions during later validation.

## 7. Privacy

For sensitive material:
- keep the source outside Git
- keep local metadata free of unnecessary personal identifiers
- use de-identified or synthetic public samples for repository demonstrations
- never treat redaction as a replacement for the preserved source

## 8. Review status

Each case must move through:

```
unreviewed -> approved
           -> rejected
```

A rejected case remains useful if rejection documents why the sample is unsuitable.

## 9. Corpus freeze

Before evaluating an engine release candidate:
1. freeze a versioned manifest
2. do not tune thresholds against hidden holdout cases
3. keep at least 20% of approved cases as a holdout set
4. record the exact engine version and configuration used for every run

## 10. Initial target

Do not claim the geometry engine is stable until at least 60 approved cases exist, with the balance requirements defined in `docs/test-taxonomy.md`.

The preferred first serious gate is 100 approved cases.
