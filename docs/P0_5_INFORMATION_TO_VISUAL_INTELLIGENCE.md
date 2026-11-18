# P0.5 — Information-to-Visual Intelligence

## Why this layer exists

The bottleneck is not the slide editor or file renderer. It is the transformation of complex business content into a semantically correct, visually legible information structure. Pitch and native PPTX remain production adapters; they do not own design reasoning.

## Runtime pipeline

1. **Content facts** — claims, entities, metrics, evidence and caveats.
2. **Information Graph** — typed nodes and typed edges; graph validation rejects dangling endpoints.
3. **Semantic family inference** — transparent baseline rules map relations to families such as causal, network, process, cycle, comparison and hierarchy.
4. **Visual Pattern retrieval** — match family, relation coverage, node capacity and density.
5. **Visual Grammar** — records composition, reading direction, edge routing, hierarchy levels, style tokens and anti-patterns.
6. **Layout candidates** — each retrieved pattern contributes structurally distinct layout hypotheses.
7. **Design ranking** — transparent heuristic score with reason strings. It is a retrieval/ranking aid, not an aesthetic truth oracle.
8. **Renderer adapter** — selected design is translated to Pitch/PPTX/HTML-specific primitives.

## Ranking contract

Current score weights:
- semantic-family fit: 40%
- relation coverage: 30%
- node capacity: 20%
- density fit: 10%

These are initial tunable defaults. They should be evaluated against a labeled reference set before being treated as production quality. Scores are explainable and can later incorporate reading-path, visual balance, overlap, typography and expert preference signals.

## Reference reverse-engineering intake

A reference record stores:
- image path and optional SHA-256 checksum
- source description
- normalized Information Graph
- Visual Grammar annotation
- inferred Pattern IDs
- analyst notes and confidence

The current pipeline is an annotation/intake contract, not automatic computer vision. OCR, element segmentation, arrow detection and relation inference are future adapters. Do not label a manually annotated reference as automatically extracted.

## Add a reference

Create a JSON record matching `schemas/reference-annotation.schema.json`. Keep the original reference image in a project-local references folder (respecting copyright and access rights). Validate it with the Pydantic model and export normalized records as a dataset.

## CLI

```bash
uv run ppt-engine rank-patterns examples/five-channel-information-graph.json
```

## First pattern families

- causal: Driver → Mechanism → Outcome
- network: Business Ecosystem
- matrix: Multi-dimensional Segmentation Matrix
- process/cycle: Multi-layer Operating Loop

A pattern is not a screenshot template. It is a semantic-to-visual contract with node capacity, relation support, visual grammar and alternative compositions.
