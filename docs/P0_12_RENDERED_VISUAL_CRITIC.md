# P0.12 — Rendered Visual Critic

## Objective

P0.12 upgrades the post-render stage from global pixel-health checks to region-level raster analysis tied back to DesignIR geometry. It is intentionally an explainable perceptual preflight, not a claim of human-level visual understanding.

## Pipeline

`DesignIR → editable PPTX → PDF → PNG → global pixel audit → region raster analysis → explainable findings → human review`.

## What is measured

- **Expected text regions:** each text node's canvas geometry is mapped to the rendered PNG using the actual image dimensions.
- **Foreground ink mask:** foreground pixels are detected relative to the local border background, allowing both dark text on light backgrounds and light text on dark panels.
- **Region occupancy:** sparse and unusually dense text regions are flagged.
- **Boundary crowding:** detected foreground ink that reaches a text region boundary is flagged as possible crowding/clipping.
- **Contrast proxy:** region luminance spread is measured; low-variation text regions are flagged for grayscale review.
- **Global visual mass:** foreground bounding-box center and four quadrant occupancy ratios are reported to identify severe composition imbalance.
- **Traceability:** region findings identify the DesignIR node and its pixel-space crop.

## CLI

Analyze a rendered PNG against its DesignIR:

```bash
uv run ppt-engine image-critic build/design_ir/compiled-slide.json \
  build/export/png/slide-1.png \
  --output build/qa/rendered-visual-critique.json
```

Or include the analysis in the full critic:

```bash
uv run ppt-engine advanced-critic build/design_ir/compiled-slide.json \
  --rendered-png build/export/png/slide-1.png \
  --output build/qa/advanced-critic.json
```

The `quality-loop` command now runs both global PNG health and region-level raster critique after export.

## Interpretation rules

- A warning is a review trigger, not an automatic design verdict.
- Full-bleed backgrounds, intentionally sparse slides, photographic regions and asymmetrical compositions may trigger false positives.
- No geometry, copy, semantic role, source reference, DataLedger value or relation is automatically changed by the image critic.
- The region analyzer does not currently apply automatic visual repairs. It provides evidence for a later repair planner.

## Known limitations

- No OCR: it cannot read the actual rendered words, detect spelling, prove text clipping at glyph level or reconstruct reading order.
- No CV object detection: it cannot recognize photos, logos, charts, icon semantics or crop quality.
- No learned multimodal model: it cannot judge taste, style fidelity, narrative effectiveness or brand compliance.
- Raster thresholds are heuristics and need calibration against real rendered decks, especially dark/full-bleed and image-heavy pages.
- Global ink center is a coarse proxy, not perceptual saliency.
- Connector path correctness is still evaluated geometrically, not semantically.

## Acceptance target

P0.12 is not considered complete merely because tests pass. It needs a curated visual benchmark of representative slide types (cover, KPI, chart, process, matrix, image-led, dense data, dark-background) with human-labeled findings, false-positive review, and before/after rendered comparisons. Human approval remains mandatory.
