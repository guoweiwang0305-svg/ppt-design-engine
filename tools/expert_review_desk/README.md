# GCL × AIA Visual Expert Review Desk

Local-first expert annotation and same-model evaluation UI for the 35-page benchmark (16 GCL + 19 AIA).

## Run locally

Download and extract the separately supplied `gcl_aia_visual_critic_review_set_0.1.zip` into this directory. It must provide `manifest.json` and `visual_test_set/*.png` alongside this `index.html`.

```bash
cd tools/expert_review_desk
python3 -m http.server 8765
```
Open http://localhost:8765. Do not use file://.

## Workflow

1. Review GCL's 16 pages first to calibrate GCL corporate visual style.
2. Review AIA's 19 pages second to calibrate information organization and diagram structures. AIA is not a GCL brand-style reference.
3. Freeze and export expert labels before exposing reviewers to model results.
4. Configure a compatible server-side VisionCritique POST endpoint.
5. Run the same model over all 35 pages. The app checks returned provider/model identity consistency.
6. Inspect FP/FN by source family and page type, export metrics, adjust one major factor at a time, then rerun the full set.

## Endpoint contract

Request JSON: `case_id`, `source_family`, `slide_type`, `image_mime_type`, `image_data_base64`, `context`.

Response JSON: `available`, `provider`, `model`, `summary`, `findings[]` with `code`, `severity`, `rationale`, `recommendation`, `confidence`, optional normalized `bbox` and `node_ids`.

Keep API keys on your server; the browser stores only the endpoint URL. Configure CORS for localhost:8765. An endpoint URL alone does not guarantee model consistency: use a pinned model/version and verify returned identity.

## Metrics

Per issue code and reviewed page: TP (both flag), FP (model only), FN (expert only). Precision, recall and F1 are computed by source family and page type. Unreviewed pages and failed model calls are excluded. Review labels and model results autosave in browser localStorage; export JSON regularly for backup.

The 35-page manifest is a pending expert-review queue, not pre-labeled ground truth. No real model inference is bundled with this static UI.
