# P0.10 — Reference-to-Production Loop

## Delivered contracts

- `production.py`: weighted page-quality scoring, Generali catalog adapter, Information Graph layout ranking, and editable semantic slot plans.
- `visual_qa.py`: deterministic DesignIR preflight for missing geometry, undersized text and overlapping elements; emits a human visual-review checklist.
- CLI commands:
  - `ppt-engine score-page review.json`
  - `ppt-engine select-layout graph.json --catalog-file visual_patterns/generali/insurance_layout_catalog.json`
  - `ppt-engine build-layout-plan graph.json gen.strategy.pillars`
  - `ppt-engine audit-design-ir design-ir.json`
- Tests cover score weighting and blocking risks, graph-based selection, slot plan traceability, and geometry/font QA.

## Page score contract

The seven dimensions are logic (20%), information value (20%), visual hierarchy (15%), density efficiency (15%), chart/diagram quality (10%), reusability (15%) and source traceability (5%). A risk mentioning factual accuracy, compliance, unreadability, illegibility or untraceable sourcing blocks an otherwise recommended score from remaining recommended.

A score is not approval. Human approval remains an explicit review action.

## Production retrieval

The Generali catalog is converted to the existing `PatternCandidate` contract and passed through `rank_patterns()`. The current ranker remains a deterministic heuristic based on inferred semantic families, relation coverage, node capacity and density. It is not a learned visual model.

## Editable layout slots

A layout plan maps Information Graph node IDs into named semantic slots from the catalog. Each slot has a stable geometry token. The plan intentionally does not invent coordinates. A future geometry resolver must bind those tokens to versioned layout geometry and validate all bounds before rendering.

## Visual QA boundary

The preflight checks DesignIR geometry and font sizes. It does not inspect rendered pixels. The report therefore always requires human review of actual exported PNGs for reading path, hierarchy, chart labels, grayscale, contrast, alignment, source legibility and visual consistency. The existing renderer/export path produces PDF and slide PNGs when LibreOffice and Poppler are installed.

## Not yet completed

- The 81 original pages have not been re-read and scored in this increment; the local data-analysis runtime was unavailable.
- No 20–30 page shortlist is claimed as human-approved.
- Slot assignment is provisional and intentionally preserves unresolved relationships.
- The renderer does not yet resolve the catalog's geometry tokens into fully composed production slides.
- Pixel-level automated QA and actual rendered-page visual inspection remain future work.
- CI/test execution has not been confirmed for the latest commits.
