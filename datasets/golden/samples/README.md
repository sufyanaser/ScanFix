# Golden Dataset Samples

This directory is intentionally empty in Git.

Real source documents MUST remain local unless they are synthetic, public-domain, or explicitly de-identified and approved for publication.

Recommended local structure:

```
samples/
  GD-001/
    source.jpg
    metadata.json
    reference/
      expected-corners.json
      notes.md
  GD-002/
    source.jpg
    metadata.json
```

Rules:
- Keep the received source file byte-for-byte unchanged.
- Record SHA-256 before any processing.
- Do not crop, rotate, recompress, rename destructively, or overwrite the source file.
- Redacted/de-identified test copies are separate derivatives, not replacements for the source.
