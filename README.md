# PPT Design Engine

A local-first, AI-assisted presentation design engine for high-end, information-dense, diagram-first business presentations.

## P0 implementation status

Implemented:
- Python package + `uv` dependency management + Typer CLI
- Pydantic v2 Design IR models and JSON Schema contract
- Page lifecycle state machine with persisted project state
- DataLedger registration, lookup, unknown-reference checks and cross-slide value consistency helper
- Native editable PPTX renderer for text, rectangles and ellipses
- LibreOffice PDF export and Poppler per-page PNG export adapters
- Pytest suite and GitHub Actions CI

Not yet implemented:
- Full-deck composition and page sequencing
- Native chart rendering, image placement/cropping and connector routing
- Region-level rendered raster critique (P0.12 heuristic; no OCR or learned vision model)
- Agent provider integration
- Pitch API adapter
- robust concurrent project locking and migration tooling

## Quick start

Requirements: Python 3.12 recommended, `uv`. For PDF/PNG export also install LibreOffice and Poppler.

```bash
uv sync --extra dev
uv run ppt-engine --help
uv run pytest
```

Validate and render a Design IR page:

```bash
uv run ppt-engine validate examples/minimal-slide.json
uv run ppt-engine render examples/minimal-slide.json --output build/demo.pptx
uv run ppt-engine export build/demo.pptx --output-dir build/export
```

## P0.5 — Information-to-Visual Intelligence

P0.5 adds typed Information Graphs, Visual Grammar contracts, a semantic Visual Pattern Library, transparent multi-candidate ranking, and a structured reference-slide annotation intake. See [P0.5 implementation spec](docs/P0_5_INFORMATION_TO_VISUAL_INTELLIGENCE.md) and run `uv run ppt-engine rank-patterns examples/five-channel-information-graph.json`.

This ranking layer is a deterministic baseline, not a claim of human-level aesthetic judgment. Reference reverse engineering currently consumes structured annotations and checks source-image integrity; automatic OCR/vision extraction is a later adapter.

## Architecture

`Content → Semantic Design IR → Design Director → Layout Candidates → Optimizer → Renderer → Visual QA → Delivery`

The Design IR is the canonical renderer-independent representation. AI makes semantic and aesthetic decisions; deterministic code validates schemas, data references, geometry and export integrity.

## Design principles

1. Logic before decoration.
2. Information relationship before template selection.
3. AI decides; deterministic code constrains and verifies.
4. Rendered output is the visual source of truth.
5. QA can reject a page.
6. Never solve density by shrinking type first.
7. Gradients and shadows are semantic tools, not automatic premium effects.
8. A layout candidate must be structurally different, not merely recolored.

## Environment notes

- PPTX rendering uses `python-pptx`.
- PDF conversion invokes `libreoffice` or `soffice`.
- PNG conversion invokes `pdftoppm` from Poppler.
- PDF/PNG export reports a clear dependency error when these executables are absent.

## P0.7 — PPTX Reference Parser

Parse editable PPTX source decks into normalized per-slide reference data:

```bash
uv run ppt-engine parse-pptx path/to/reference.pptx --output build/reference/reference.json
```

Extracts native text runs, geometry, shape/group hierarchy, fill/line styles, image crop metadata and connector geometry. See `docs/P0_7_PPTX_REFERENCE_PARSER.md` for boundaries and semantics-safety rules.

## P0.8 — Design Pattern Mining

Mine recurring structures from P0.7 parser output and maintain an expert review ledger:

```bash
uv run ppt-engine mine-patterns build/reference/reference.json --min-frequency 2
uv run ppt-engine review-pattern mined.horizontal.001 --decision accept --notes "Clear hierarchy"
```

See [P0.8 implementation notes](docs/P0_8_DESIGN_PATTERN_MINING.md). Mining candidates remain unapproved until an expert accepts them.


## P0.9 — Visual Pattern Intelligence

Extract interpretable visual feature vectors from P0.7 parsed decks:

```bash
uv run ppt-engine extract-visual-features build/reference/gcl.json build/reference/aia.json --output build/visual_intelligence/features.json
```

P0.9 adds approximate occupancy/whitespace, weighted visual center, focal dominance, image/text ratios, alignment regularity, typography hierarchy, editable palette and chart/table mix. Similarity is transparent and deterministic (geometry 35%, composition 20%, typography 15%, color 15%, content mix 15%). It is not a learned aesthetic model. Only expert-approved P0.8 patterns with explicit semantic mappings can enter production retrieval.

See docs/P0_9_VISUAL_PATTERN_INTELLIGENCE.md and design_profiles/generali_corporate.json.


## P0.9B — Generali Insurance Layout, Chart and Icon Rules

P0.9B adds a 13-family insurance layout catalog, an analytical-question-first chart grammar, a semantic icon registry with provenance/licensing requirements, and a page-quality scoring schema for expert review.

- `visual_patterns/generali/insurance_layout_catalog.json`
- `visual_rules/charts/insurance_chart_grammar.json`
- `visual_rules/icons/insurance_icon_registry.json`
- `schemas/page-quality-score.schema.json`

See [P0.9B implementation notes](docs/P0_9B_GENERALI_LAYOUT_CHART_ICON_RULES.md). These are candidate design specifications; mined reference pages require individual scoring and human approval before production use.


## P0.10A — Reference Page Assetization

The 81-page source corpus (21 GCL + Alleanza pages and 60 AIA training pages) was reopened and reprocessed. The local review package contains per-page feature/score records, a visually inspected 28-page balanced candidate shortlist, page thumbnails and traceable pattern-seed mappings. Scores are heuristic screening aids; candidates remain pending user/expert approval. Source PPTX files and extracted business text are not committed to this repository.

See [P0.10A reference assetization](docs/P0_10A_REFERENCE_ASSETIZATION.md).

## P0.10B — Geometric Layout Compilation

A versioned 16:9 geometry catalog now defines slot rectangles for the 13 Generali insurance layout families. The compiler can map an Information Graph to a slot plan and then to editable DesignIR. Metric nodes must carry DataLedger references. The renderer draws explicit graph relations, and rendered PNGs have a basic pixel-health audit.

```bash
uv run ppt-engine compile-layout graph.json gen.kpi.executive_dashboard
uv run ppt-engine validate build/design_ir/compiled-slide.json
uv run ppt-engine render build/design_ir/compiled-slide.json --output build/slide.pptx
uv run ppt-engine export build/slide.pptx --output-dir build/export
uv run ppt-engine audit-design-ir build/design_ir/compiled-slide.json
uv run ppt-engine audit-rendered-png build/export/png/slide-1.png
```

See [P0.10B layout compiler](docs/P0_10B_GEOMETRY_LAYOUT_COMPILER.md). Current slot geometry and connector routing are first-pass deterministic scaffolds and still require visual tuning and human acceptance.


## P0.11 — Layout Optimization & Visual Critic

P0.11 adds a bounded, explainable optimizer and critic API:

- `optimize_layout(ir, max_iterations=2)` performs conservative text-fit adjustments only, never crossing the configured minimum font size.
- The critic diagnoses missing geometry, overlap, likely text overflow, undersized type and crude focal-area dominance.
- Every automatic repair records node ID, before/after values and rationale.
- Overlaps are reported for deliberate re-layout; nodes are not silently moved because that can break relation geometry and reading order.
- Copy, facts, metrics, source references, semantic relations and reading order are not rewritten by the optimizer.
- Human visual review remains mandatory; pixel metrics are not treated as visual understanding.

See [P0.11 Layout Optimization & Visual Critic](docs/P0_11_LAYOUT_OPTIMIZATION_VISUAL_CRITIC.md). API: `ppt_engine.optimization.optimize_layout`.

```bash
uv run ppt-engine optimize-layout build/design_ir/compiled-slide.json \
  --output build/design_ir/optimized-slide.json \
  --report-output build/qa/visual-critic.json \
  --max-iterations 2
```


## P0.11.2 — Advanced Visual Critic

Run explainable geometry, hierarchy, relation-routing and density checks, optionally including the rendered PNG pixel audit:

```bash
uv run ppt-engine advanced-critic build/design_ir/optimized-slide.json \
  --rendered-png build/export/png/slide-1.png \
  --output build/qa/advanced-critic.json
```

Python API: `ppt_engine.advanced_critic.critique_slide`. Geometry repairs are suggestions only; orthogonal routes are returned as proposals and do not silently mutate DesignIR. Density warnings recommend a primary/secondary split but never split or delete content automatically. Human review remains mandatory.


### End-to-end render and critic loop

```bash
uv run ppt-engine quality-loop build/design_ir/compiled-slide.json \
  --output-dir build/quality \
  --max-rounds 4
```

This produces editable PPTX, PDF, PNG, final DesignIR and a structured critic report. Only bounded text-fit adjustments are automatic; geometry changes and slide splits remain reviewable suggestions.


## P0.12 — Rendered Visual Critic

P0.12 analyzes actual rendered PNG pixels and maps the results back to DesignIR text regions. It measures region ink occupancy, edge crowding, contrast proxies, global visual mass and quadrant density. It supports light text on dark panels using local-background foreground detection.

```bash
uv run ppt-engine image-critic build/design_ir/compiled-slide.json \
  build/export/png/slide-1.png \
  --output build/qa/rendered-visual-critique.json

uv run ppt-engine quality-loop build/design_ir/compiled-slide.json \
  --output-dir build/quality \
  --max-rounds 4
```

This is an explainable raster preflight, not OCR or a learned vision model. It cannot verify wording, chart semantics, photo crop meaning or aesthetic quality. Findings are reviewable evidence; no geometry or content is silently rewritten. See [P0.12 Rendered Visual Critic](docs/P0_12_RENDERED_VISUAL_CRITIC.md).
