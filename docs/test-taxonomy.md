# Golden Dataset Taxonomy

The dataset must represent failure modes seen in real administrative-document photography, not ideal scanner samples.

## Geometry
- clean
- mild-perspective
- severe-perspective
- rotation
- deskew
- curved-page
- folded-page
- partial-page
- occluded-edge
- hand-visible

## Boundary detection
- weak-boundary
- white-on-white
- busy-background

## Illumination and capture
- strong-shadow
- uneven-lighting
- underexposed
- overexposed
- motion-blur
- focus-blur
- jpeg-compression
- low-resolution

## Content integrity
- colored-stamp
- faint-stamp
- signature
- handwriting
- table
- thin-lines
- carbon-copy
- mixed-arabic-latin
- eastern-arabic-digits

## Minimum initial corpus

Target: 60–100 cases before declaring the geometry engine stable.

At minimum:
- 10 clean / mild cases
- 10 severe perspective / weak-boundary cases
- 10 lighting / shadow cases
- 10 WhatsApp compression / low-resolution cases
- 10 stamp/signature/thin-line cases
- 10 failure-intent cases where automatic processing SHOULD stop and request review

Cases may carry multiple taxonomy tags.

## Dataset balance rules
1. Do not let easy cases exceed 40% of the corpus.
2. At least 20% of the corpus must intentionally require manual review.
3. At least 20 cases must contain elements that would expose destructive processing: stamps, signatures, faint text, thin table borders, handwriting, or carbon copies.
4. Include both Arabic-only and mixed Arabic/Latin documents.
5. Include Eastern Arabic numerals in a meaningful subset.
6. Do not use confidential real documents in the public repository.
