# P0.12.1 — GCL × AIA Expert Review and Model Benchmark

## Objective
Build a controlled human-labeled benchmark, run one pinned vision model over the same 35 pages, analyze errors and improve it with before/after evidence.

## Required sequence
1. Review GCL's 16 pages and establish a GCL-specific corporate visual-style baseline.
2. Review AIA's 19 pages and establish information organization and diagram-structure baselines.
3. Freeze expert labels before exposing model output.
4. Run the same provider/model/version, prompt, parameters and thresholds on all 35 pages.
5. Compare predictions with adjudicated expert labels by family, page type and issue code.
6. Optimize prompt/taxonomy/thresholds and rerun all 35 pages; preserve the original run.

## Separation of standards
GCL assesses brand palette discipline, typography, composition, hierarchy, chart/diagram craft, whitespace, image treatment and cross-page consistency. AIA assesses narrative logic, information hierarchy, relationship encoding, chart/data clarity, density, evidence context, readability and structural reusability. AIA is not a GCL brand-style reference.

## Blind review
Experts independently record issue codes, severity, evidence/location, reviewer and notes. Adjudicate disagreements, then freeze/export labels. Never overwrite expert truth with model output. Pending pages are not negative examples.

## Metrics
TP: expert and model both flag. FP: model only. FN: expert only. Precision=TP/(TP+FP); Recall=TP/(TP+FN); F1=2PR/(P+R). Report raw counts and normalized rates by family × page type × issue code. Exclude unreviewed pages and failed model calls.

## Optimization
Rank error concentrations, inspect representative pages, identify whether cause is taxonomy, prompt, visual evidence, page-type mismatch or model capability. Change one major factor at a time, version it, rerun all 35 pages and compare FP/FN, precision, recall, F1 and regressions across both families.

## Current execution status (2026-11-19)
- All 16 GCL pages and 19 AIA pages received a provisional GPT-6 visual expert pass in the prescribed order.
- Labels, issue evidence and per-page notes are stored in `tools/expert_review_desk/manifest.json`.
- GCL profile quality gates were updated from the provisional GCL review.
- Reusable information structures from AIA were extracted into `reference_data/aia_information_structure_patterns.json`; these are structure references only, not GCL styling.
- The review set is not independently human-adjudicated gold truth yet.
- No separate batch vision endpoint is configured, so model predictions and FP/FN are still pending. Do not treat blank `observed_issue_codes` as model negatives or score the current manifest as a completed model benchmark.

## Truth status
The current labels are provisional AI-assisted expert annotations. Human adjudication and a real, pinned provider/model run are required before reporting measured model accuracy.
