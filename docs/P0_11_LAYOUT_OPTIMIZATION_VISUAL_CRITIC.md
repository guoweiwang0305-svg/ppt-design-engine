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
