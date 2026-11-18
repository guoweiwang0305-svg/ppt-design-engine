# Layout Intelligence

## Supported semantic grammars

| Relationship | Primary layout | Alternatives |
|---|---|---|
| sequence | directional process | swimlane, decision tree |
| hierarchy | layered architecture | tree topology |
| comparison | matrix / contrast bridge | parallel tracks |
| cycle | operating loop | double-loop |
| network | topology | hub-and-spoke |
| composition | decomposition | stacked structure |
| distribution | matrix / map | small multiples |
| evidence | thesis-evidence chain | data narrative |

## Layout algorithm

1. Estimate node dimensions from actual text and font metrics.
2. Build a logical grid.
3. Generate candidate regions.
4. Place primary thesis/anchor.
5. Place groups.
6. Place relationships/connectors.
7. Run collision and overflow constraints.
8. Calculate density, whitespace, center of gravity and reading path.
9. Rank candidates.
10. Return top candidate + diagnostics.

## Constraints

- minimum readable font is a style/project constraint, never a hidden fallback.
- no connector may pass through a text node.
- related nodes should share alignment axes where possible.
- visual emphasis must correlate with semantic importance.
- node count should trigger clustering or alternate grammar before typography is reduced.

## Diagnostics

Every candidate returns:
- density_score
- whitespace_score
- balance_score
- collision_count
- overflow_count
- hierarchy_score
- reading_path_score
- semantic_fidelity
- style_fit
