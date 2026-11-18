# P0.10B — Geometric Layout Compilation and Render QA

## Geometry catalog

`visual_patterns/generali/layout_geometry.json` provides versioned, editable slot rectangles for each of the 13 Generali insurance layout families. Coordinates use the 13.333 × 7.5 inch 16:9 canvas. Slot geometry is explicit; the compiler refuses to invent positions if a required slot has no geometry.

The current geometry is a first-pass scaffold designed to prove the production contract. It is not a pixel-perfect reconstruction of the 28 reference slides. Each family requires visual tuning after actual content is placed.

## Information Graph to DesignIR

`build_layout_plan` binds graph nodes to named semantic slots and retains all graph edge IDs/relations for QA. `layout_plan_to_design_ir` then:

1. Adds the page thesis as an editable headline node.
2. Binds each assigned InformationNode to a slot rectangle.
3. Splits multi-item slots by stack, grid or horizontal arrangement.
4. Maps node kinds to semantic roles and importance.
5. Preserves evidence references and DataLedger data refs.
6. Converts graph edges into DesignIR relations only when both endpoints are present.

Metric nodes require a DataLedger `data_ref`; the compiler refuses to render an unregistered metric value.

## CLI workflow

```bash
uv run ppt-engine select-layout graph.json
uv run ppt-engine compile-layout graph.json gen.kpi.executive_dashboard
uv run ppt-engine validate build/design_ir/compiled-slide.json
uv run ppt-engine render build/design_ir/compiled-slide.json --output build/slide.pptx
uv run ppt-engine export build/slide.pptx --output-dir build/export
uv run ppt-engine audit-design-ir build/design_ir/compiled-slide.json
uv run ppt-engine audit-rendered-png build/export/png/slide-1.png
```

## Rendered-image QA

The renderer now draws graph relations as connectors before drawing nodes, so nodes remain visually in front. The rendered PNG audit measures dimensions, near-blank output, sampled color diversity and global luminance spread. These pixel statistics are only a technical preflight; they cannot establish semantic correctness, text legibility or aesthetic quality.

Every page still requires human inspection at presentation size, contact-sheet review, 100% zoom on chart labels and footnotes, grayscale/contrast review, source/data checks and final acceptance.

## Failure handling

- Missing slot geometry: compilation is blocked; do not guess.
- Missing required semantic content: report an unfilled slot.
- Metric without DataLedger ref: compilation fails.
- Node outside canvas or overlapping content: DesignIR validation / QA reports the problem.
- Unresolved graph edge: preserve the relation and flag connector routing; do not silently discard it.
- Rendered image nearly blank: pixel QA blocks the page.
- Low contrast or small render: QA warning; human review required.

## Known limitations

- Current slot binding is conservative and partly order-based; it is not yet a learned semantic layout planner.
- Slot containers are split by simple grid/stack rules; no collision optimizer or typography fitting engine yet.
- Relationship connectors are straight center-to-center lines, not orthogonally routed and not edge-avoiding.
- PNG statistics do not perform OCR, object detection, text overflow detection or perceptual scoring.
- Latest tests and CI must be run before calling the pipeline production-ready.
