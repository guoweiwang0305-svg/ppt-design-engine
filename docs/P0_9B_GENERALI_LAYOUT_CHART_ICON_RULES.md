# P0.9B — Generali Insurance Layout, Chart and Icon Rules

## Purpose

This increment turns the Generali corporate reference profile into reusable, machine-readable design specifications. It adds a layout catalog, chart decision grammar, semantic icon registry and a page-quality review contract.

These are **candidate rules**, not official Generali brand standards and not a claim that every rule was extracted from the user's two source decks. Official Generali investor materials ground the corporate visual direction and business-reporting patterns; the user-provided GCL and AIA decks ground the local insurance context; consulting presentation taxonomies inform some structural patterns.

## 1. Layout catalog

File: `visual_patterns/generali/insurance_layout_catalog.json`

The catalog currently defines 13 layout families:

1. Executive KPI dashboard
2. Multi-business-line small multiples
3. Market ranking and competitive position
4. Regional presence and operating coverage
5. Customer segmentation
6. Customer tagging taxonomy
7. OMO channel loop
8. Ecosystem value exchange
9. Strategy pillars and capabilities
10. Product/lifecycle needs matrix
11. Health service ecosystem
12. Operating driver / issue tree
13. Financial variance bridge

Each pattern defines when to use it, semantic families, relationship types, capacity ranges, composition, slots, chart choices, density, rules and anti-patterns. Retrieval should match the information graph first, then apply style tokens. Do not select a pattern because its color resembles Generali.

## 2. Chart grammar

File: `visual_rules/charts/insurance_chart_grammar.json`

The chart selector follows:

`analytical question → data shape → comparison scope → chart family → encoding → labels → integrity checks → source`

The rule set covers time series, category contribution, composition, multi-metric comparison, ranking, geography, variance bridge, customer matrices, conversion funnels and channel journeys.

Insurance-specific metric context is mandatory. For example, gross written premium needs gross/net, written/earned, period, currency and scope; combined ratio needs P&C scope and discounted/undiscounted basis; solvency ratio needs regulatory regime, entity and period end. DataLedger remains the source of truth for numeric values.

## 3. Icon registry

File: `visual_rules/icons/insurance_icon_registry.json`

Icons are semantic assets, not decorative fillers. The registry defines consistent outline-family tokens, stroke widths, optical sizes, semantic categories and required provenance metadata (asset path, license, source, version and approval).

If no exact icon exists, prefer a labeled geometric node over an invented or misleading pictogram. Do not redraw Generali's protected lion emblem as a generic icon.

## 4. Page-quality scoring contract

File: `schemas/page-quality-score.schema.json`

Each reference page can be reviewed on seven dimensions, each 0–5:

| Dimension | What the reviewer judges |
|---|---|
| Logic | Does the page express a coherent argument or relationship? |
| Information value | Does it contain useful evidence, not filler? |
| Visual hierarchy | Is the reading path obvious? |
| Density efficiency | How much relevant information is understood per unit of visual space? |
| Chart/diagram quality | Is the visual encoding analytically appropriate and legible? |
| Reusability | Can its underlying structure transfer to other business content? |
| Source traceability | Can claims and numbers be traced to reliable sources? |

Recommended weighting for the human-review rubric: logic 20%, information value 20%, visual hierarchy 15%, density efficiency 15%, chart/diagram quality 10%, reusability 15%, source traceability 5%.

Decision thresholds are review guidance, not automatic approval:
- 4.2–5.0: recommended candidate
- 3.2–4.19: revise / selectively reuse
- below 3.2: reject as a reusable exemplar

A high numeric score cannot override a factual, compliance or legibility failure. Final status must be human-reviewed; only an explicit expert approval can make a pattern production-eligible.

## 5. 81-page mining workflow

The two source decks are 60 + 21 = 81 pages. The intended process is:

1. Parse every slide from the original editable PPTX.
2. Extract visual feature vectors (geometry, text/image mix, whitespace, typography, color, chart/table presence).
3. Group near-duplicate structures into candidate pattern families.
4. Create one page-quality record per source slide.
5. Rank candidates within each family; do not compare all page genres on one global score alone.
6. Select 20–30 exemplars with diversity constraints (avoid selecting 20 nearly identical KPI pages).
7. Human-review each candidate as recommended, revise or reject.
8. Only approved examples feed the production pattern adapter.

Important: automatic feature extraction can support a pre-screen, but it cannot infer whether a slide's argument is correct, evidence is sufficient, or density is cognitively efficient. Those require content-aware and human review.

## 6. Known limitations

- The 81 original slides have not been re-scored in this increment because the local data-analysis runtime was unavailable.
- The catalog contains candidate design specifications, not page-by-page reverse-engineered replicas.
- Chart and icon rules are contracts; the renderer does not yet implement all chart families or asset resolution.
- The page-quality schema defines the review payload; a scoring CLI and review UI are future implementation tasks.
- The color values in the Generali profile remain engineering approximations, not an official brand book.
