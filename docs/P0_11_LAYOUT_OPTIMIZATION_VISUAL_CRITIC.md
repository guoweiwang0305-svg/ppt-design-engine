# P0.11 — Layout Optimization & Visual Critic

## Goal
Add a bounded optimization loop between DesignIR compilation and final visual acceptance:
`DesignIR → deterministic preflight → safe repair → visual critic → render → pixel audit → human acceptance`.

## What is automated
- Estimate text capacity from node geometry, font size and canvas units.
- Apply conservative one-point font reductions only when estimated text capacity is exceeded, never below `DesignConstraints.min_font_pt`.
- Detect missing geometry, low type size, likely overflow and overlapping nodes.
- Report severity, affected node IDs, diagnosis, recommended next action and whether a repair is safe to automate.
- Flag a crude single-element area dominance proxy for human inspection.

## What is deliberately not automated
- No automatic moving of overlapping nodes: this can break causal/sequence reading order and relation geometry.
- No rewriting, deleting, summarizing or changing semantic importance of content.
- No automatic chart scale/unit changes, data changes, source changes or relation changes.
- No claim that pixel statistics equal visual understanding. OCR/VLM review and expert aesthetic acceptance are future capabilities.

## API
`optimize_layout(ir, max_iterations=2, min_font_pt=None) → OptimizationResult`

The input DesignIR is not mutated. The output includes a repaired DesignIR and a `VisualCriticReport`. Iterations are bounded (0–5); every font adjustment is recorded. Decisions are `blocked`, `revise`, or `accept_for_human_review`. Even the last decision still requires human review.

## CLI workflow
After compiling a slide, run:
```bash
uv run pytest
```
The Python API is available from `ppt_engine.optimization`. CLI wiring is intentionally deferred until the optimization report contract is exercised by tests; this avoids exposing a command that has not yet been validated end-to-end.

## Acceptance criteria
- Input DesignIR remains unchanged.
- No font falls below the configured minimum.
- Every automatic adjustment is recorded with before/after values and rationale.
- Overlaps are diagnosed, never silently repositioned.
- Semantic relations and reading order are preserved.
- Human review remains mandatory.


# P0.11.2 — Advanced Visual Critic

## Diagnostic pipeline
`DesignIR → geometry preflight → hierarchy critique → connector routing → density/split assessment → optional rendered PNG audit → human acceptance`.

## Geometry collision repair
`propose_collision_repairs(ir)` proposes safe single-node translations (right/left/down/up) that clear current node collisions and respect a canvas safe margin. If no translation is feasible, it recommends group reflow or a page split. Suggestions are advisory and never mutate DesignIR; the orchestrator must validate reading order and relation semantics before applying one.

## Visual hierarchy
The first rule set checks for exactly one thesis node, competing font sizes, and underweighted critical metrics. These are explainable heuristics, not learned saliency or taste judgments. Brand style and narrative intent can legitimately override a numeric warning.

## Orthogonal connector routing
`route_relations_orthogonal(ir)` finds a shortest collision-free Manhattan route among direct, two-bend and obstacle-boundary detour candidates. It reports `routed`, `blocked`, or `missing_endpoint`. The route points are consumed by the PPTX renderer as editable straight line segments forming an orthogonal path; the renderer does not rewrite DesignIR connector geometry. If all candidate paths are blocked, it omits that connector rather than drawing through an obstacle. Complex multi-edge crossings, port selection, arrowhead semantics and global route optimization remain future work.

## Rendered-image recheck
`critique_slide(ir, rendered_png=...)` adds pixel health checks from the rendered PNG (blankness, global contrast, resolution). This is a post-render sanity check, not OCR or image understanding. It cannot verify text clipping, legibility, aesthetic balance or brand fidelity.

## Page split recommendation
Density heuristics combine node count, text volume, summed bounding-box area and long text blocks. When risk is high, the report separates primary/thesis/critical nodes from secondary nodes. It proposes a grouping; it does not duplicate or remove content automatically.

## CLI
```bash
uv run ppt-engine advanced-critic build/design_ir/optimized-slide.json \
  --rendered-png build/export/png/slide-1.png \
  --output build/qa/advanced-critic.json
```

## Safety and acceptance
- No copy, data, source reference, semantic role, relation or reading order is rewritten.
- Geometry suggestions are never applied without rechecking all nodes and edges.
- Connector routes are advisory geometry, not persisted connector edits.
- A density warning triggers content/layout review, not an automatic split.
- Human review remains mandatory even when the report says `accept_for_human_review`.

## Known limits
No OCR/VLM, no image segmentation, no true font metrics, no global multi-edge routing, no semantic text compression, no deck-level rhythm model. The area occupancy measure is a summed bounding-box proxy and may double-count overlaps.


## P0.11.3 — End-to-end quality loop

The `quality-loop` command runs a bounded pass from DesignIR to final rendered assets:

```bash
uv run ppt-engine quality-loop build/design_ir/compiled-slide.json \
  --output-dir build/quality \
  --max-rounds 4
```

For metric nodes backed by DataLedger:

```bash
uv run ppt-engine quality-loop build/design_ir/compiled-slide.json \
  --output-dir build/quality \
  --max-rounds 4 \
  --ledger-file build/data_ledger.json
```

The loop applies only conservative text-fit font adjustments (one point per round, bounded by the minimum font size), then renders editable PPTX, exports PDF/PNG, and runs the advanced critic against the rendered PNG. It writes the final DesignIR and a complete quality-loop report. Geometry proposals, page splits and content changes remain review tasks; they are not auto-applied.

Required local executables for export: LibreOffice and Poppler `pdftoppm`. If export is unavailable, the CLI reports the dependency failure rather than claiming a complete visual review.
