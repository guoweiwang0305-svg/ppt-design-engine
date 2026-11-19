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


## Optional OCR verification

If the Tesseract executable is installed, the Advanced Critic also runs OCR over the rendered PNG and maps recognized word boxes back to DesignIR text regions. It reports missing/partial text and words that cross a region boundary. The CLI accepts the same DataLedger used by the renderer so metric nodes are compared against their resolved displayed values:

```bash
uv run ppt-engine advanced-critic build/design_ir/compiled-slide.json \
  --rendered-png build/export/png/slide-1.png \
  --ledger-file build/data_ledger.json \\
  --ocr-language chi_sim+eng
```

Tesseract is optional. If unavailable, the report explicitly records `ocr_unavailable`. OCR language defaults to English; use `--ocr-language chi_sim+eng` for Chinese/English when the corresponding Tesseract language data is installed. OCR findings are advisory because stylized type, small labels and charts can produce false positives.


## Human-labeled calibration benchmark

A critic must be evaluated against human judgment before its warnings are trusted. P0.12 adds a benchmark format and scorer:

```bash
uv run ppt-engine score-visual-benchmark examples/visual_critic_benchmark.template.json \
  --output build/qa/visual-benchmark-score.json
```

Each case records the slide type, expert-expected issue codes and critic-observed issue codes. The scorer reports precision, recall, F1, false positives, missed issues and per-slide-type metrics. The included file is only a template, not a populated benchmark; it must be filled using expert-reviewed rendered slides before thresholds are calibrated.


## P0.12.1 — Full-slide vision adapter and transactional repair

The Advanced Critic now exposes a provider-neutral multimodal adapter contract in
`ppt_engine.vision_adapter`. A deployment provider receives the complete rendered
PNG plus slide thesis, style profile reference, canvas and node context. It returns
structured findings for composition, hierarchy, chart expression, image crop,
density, style consistency and legibility. Each finding includes severity,
confidence and optional normalized page coordinates.

No model vendor, endpoint, API key or network client is bundled. Without a configured
provider, the report explicitly returns `available=false`; this is not a pass.
A production deployment must implement `VisionCriticProvider` and satisfy its
data-handling/privacy requirements. Pixel and OCR checks remain auxiliary evidence.

### Real source-page review queue

`reference_data/gcl_aia_visual_critic_review_queue_2026-11-19.json` indexes 35
actual rendered pages selected from the user's uploaded source decks (16 GCL and
19 AIA). The separate ZIP `gcl_aia_visual_critic_review_set_0.1.zip` contains
full-slide PNGs and a review manifest. The pages cover covers/closing, charts,
data tables, matrices, process diagrams, taxonomy, maps, dashboards, ecosystems
and image-led compositions.

All 35 cases are explicitly marked `pending_expert_review`. They are a real
visual review queue, **not yet a labeled benchmark**. Precision, recall and F1
must not be reported until expert labels and model-observed issue codes are
entered. The benchmark scorer now excludes pending cases and reports their count.
GCL style consistency must be judged against GCL only; AIA is an information
structure reference, not a GCL brand reference.

### Transactional before/after repair gate

The quality loop renders baseline and candidate versions separately, runs the
same critic on both, and calls `compare_repair_reports`. A candidate is accepted
only when weighted issue severity decreases and no blocker/major finding is
introduced or increased. Otherwise the original DesignIR is restored and the
report records `repair_rejected_and_rolled_back`. Equal scores are not accepted.
Every accepted repair still requires human review.

The current comparison gate is conservative and code/node based; it does not
prove aesthetic improvement if no vision provider is configured. A provider
finding is only meaningful when the provider is actually available and its
evaluation policy is calibrated.
