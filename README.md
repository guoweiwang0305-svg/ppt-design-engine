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
- Automated visual critique / perceptual QA
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