# P0.8 — Design Pattern Mining

## Objective
Turn a collection of parsed PPTX slides into a reviewable library of recurring visual structures. Mining produces candidates, not automatic design truth. Expert approval is the gate for production use.

## Pipeline
1. Parse source PPTX with P0.7 into normalized JSON.
2. Extract per-slide features: element counts, text/shape/image/connector counts, density bucket, composition family, approximate alignment signature, color signature and typography signature.
3. Cluster by deterministic structural signature. Each cluster becomes a MinedPattern with frequency, source slide references, feature summary and confidence.
4. Expert reviews each candidate as accept, reject or revise. Reviews are append-only JSONL records.
5. Re-run mining with the review ledger to materialize approved/rejected/revision_required status and any revised name/family.

## Commands
```bash
uv run ppt-engine parse-pptx reference.pptx --output build/reference/reference.json
uv run ppt-engine mine-patterns build/reference/reference.json other/reference.json --min-frequency 2
uv run ppt-engine review-pattern mined.horizontal.001 --decision accept --notes "Strong hierarchy and clear reading path"
uv run ppt-engine review-pattern mined.central_or_grid.002 --decision revise --revised-name "Asymmetric evidence grid" --revised-family "distributed" --notes "Retain content grouping, reduce equal-weight cards"
```

## Expert review protocol
- accept: pattern is reusable and structurally sound.
- reject: pattern should not enter the approved retrieval set.
- revise: preserve as a candidate but record the required correction; revised labels can be applied through the ledger.
- Use reason codes such as `clear_hierarchy`, `strong_reading_path`, `good_density`, `weak_hierarchy`, `decorative_noise`, `over_cardified`, `poor_alignment`, `ambiguous_relationship`, `low_reusability`.

## Important limitations
- This version uses exact structural signatures, not learned embeddings or visual similarity models.
- Composition and density are heuristic buckets; they are useful for indexing, not aesthetic judgments.
- Color and typography signatures are descriptive metadata; the first clustering pass does not yet split patterns by style.
- The parser's extracted features inherit P0.7 limitations (theme colors, group transforms, connector endpoint fidelity, SmartArt and chart internals).
- No real user reference deck has been added to this repository dataset yet. Tests use synthetic PPTX-like JSON fixtures.

## Acceptance criteria
- Identical synthetic slide structures cluster together.
- Pattern frequency and provenance are preserved.
- Review records are append-only.
- Accept/reject/revise state is reproducible by replaying the ledger.
- No mined candidate is treated as expert-approved by default.