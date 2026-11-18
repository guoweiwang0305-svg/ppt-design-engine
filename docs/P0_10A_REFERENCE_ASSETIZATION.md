# P0.10A — Insurance Reference Page Assetization

## Source materials reopened

The two source presentations were reopened from the user's Library and the prior parsed reference dataset was re-extracted:

- GCL + Alleanza Assicurazioni: 21 slides.
- AIA savings-insurance training deck: 60 slides.
- Total: 81 slides.

The original PPTX binaries and full extracted business text are not committed to this repository. A local review package contains page images and extracted feature summaries for the user.

## Page inventory

Every page receives a stable ID: `GCL:slide-01` ... `GCL:slide-21`, or `AIA:slide-01` ... `AIA:slide-60`. The inventory stores source filename, slide number, title text, geometry-derived occupancy, whitespace, font statistics, element counts, image/chart/table/connector counts, semantic family, seven score dimensions, weighted score, and risk flags.

The seven dimensions and weights are:

| Dimension | Weight |
|---|---:|
| Logic quality | 20% |
| Information value | 20% |
| Visual hierarchy | 15% |
| Density efficiency | 15% |
| Chart/diagram quality | 10% |
| Reusability | 15% |
| Source traceability | 5% |

The scores are transparent heuristic screening estimates, not human ground truth. The source parser does not infer every semantic relation, sample raster colors, or measure text legibility from the actual display. Scores must not be represented as expert approval.

## Visual candidate review

A 28-page balanced shortlist was visually inspected from rendered page contact sheets: 14 GCL and 14 AIA pages. Candidate pages cover KPI, growth, ranking, regional footprint, customer segmentation/tagging, acquisition, OMO, product architecture, health ecosystem, operating model, service layers, digital workflow, wealth segmentation, and training frameworks.

Each candidate stores a thumbnail path, source slide trace, candidate pattern ID, assistant visual-review note, automated score and risk flags. Status remains `pending_user_approval`; assistant review is not a substitute for user/expert approval.

## Pattern seed conversion

`reference_pattern_seeds.json` maps reference pages to semantic production patterns. Source style and semantic pattern are kept separate: GCL pages use the Generali corporate profile; AIA pages retain their warm-neutral wealth-training style. AIA pages may teach information structures without being rebranded as official Generali visual references.

## Review package

The generated ZIP is a local deliverable and is not committed here because source presentations may contain proprietary business material. It contains the 81-page inventory, scoring CSV/JSON, 28 candidate images, candidate review records, pattern seed mapping and source analysis note.
