# GCL × AIA Visual Expert Review Desk

Local-first expert annotation and same-model evaluation UI for the 35-page benchmark (16 GCL + 19 AIA).

## Run locally

1. Clone/download this repository.
2. Download the separate image bundle `gcl_aia_visual_critic_review_set_0.1.zip` previously supplied in this conversation.
3. From this directory, extract the bundle. It creates `visual_test_set/` with the 35 PNGs and its source manifest. Copy the manifest to the app root:

   ```bash
   unzip /path/to/gcl_aia_visual_critic_review_set_0.1.zip -d .
   cp visual_test_set/manifest.json manifest.json
   ```

   The repository also includes `manifest.json`; the copy command above uses the bundle's image-matched manifest.
4. Start the local server:

   ```bash
   python3 -m http.server 8765
   ```

5. Open http://localhost:8765. Do not use file://.

## Workflow

1. Review GCL's 16 pages first to calibrate GCL corporate visual style.
2. Review AIA's 19 pages second to calibrate information organization and diagram structures. AIA is not a GCL brand-style reference.
3. Freeze and export expert labels before exposing reviewers to model results. Model execution is blocked until all 35 pages are reviewed.
4. Configure a compatible server-side VisionCritique POST endpoint.
5. Run the same model over all 35 pages. The app checks returned provider/model identity consistency and rejects missing identity fields.
6. Inspect FP/FN by source family and page type, export metrics, adjust one major factor at a time, then rerun the full set.

## Endpoint contract

Request JSON: `case_id`, `source_family`, `slide_type`, `image_mime_type`, `image_data_base64`, `context`.

Response JSON: `available`, `provider`, `model`, `summary`, `findings[]` with `code`, `severity`, `rationale`, `recommendation`, `confidence`, optional normalized `bbox` and `node_ids`.

Keep API keys on your server; the browser stores only the endpoint URL. Configure CORS for localhost:8765. Pin the model/version; the batch checks returned provider/model identity across responses.

## Metrics and product integration

Per issue code and reviewed page: TP (both flag), FP (model only), FN (expert only). Precision, recall and F1 are computed by source family and page type. Unreviewed pages and failed model calls are excluded. Review labels and model results autosave in browser localStorage; export JSON regularly.

The exported JSON can be passed directly to the repository scorer:

```bash
uv run ppt-engine score-visual-benchmark expert-review.json \
  --output build/qa/gcl-aia-visual-benchmark.json
```

The CLI filters the app's extended case metadata to the benchmark schema and reports both page-type and source-family × page-type metrics.

The 35-page manifest is a pending expert-review queue, not pre-labeled ground truth. No real model inference is bundled with this static UI.

## Run the real batch model from the project CLI

The repository now includes an OpenAI-compatible multimodal provider and a reproducible CLI runner. It requires an API endpoint that supports chat-completions image input and JSON output. Configure credentials only in your local shell:

```bash
export PDE_VISION_API_BASE="https://your-provider.example/v1"
export PDE_VISION_API_KEY="..."
export PDE_VISION_MODEL="your-pinned-vision-model-id"
export PDE_VISION_PROVIDER="provider-and-deployment-name"
```

From the repository root, after extracting the 35 PNGs into `tools/expert_review_desk/visual_test_set/`:

```bash
uv run ppt-engine run-vision-benchmark \
  tools/expert_review_desk/manifest.json \
  tools/expert_review_desk/visual_test_set \
  --output build/qa/gcl-aia-vision-benchmark.json
```

The runner refuses to start while any page is pending expert review, verifies that provider/model identity stays constant across the batch, uses temperature 0, saves each full model response, and emits a scored report with source-family × slide-type metrics. If a request fails or the model identity changes, the run stops rather than silently mixing models.

For a custom vendor, implement the `VisionCriticProvider` protocol or expose an OpenAI-compatible `/chat/completions` endpoint. API keys must never be committed to Git or placed in the static review UI. Provider-specific image detail, token limits, retention and data residency remain the user's responsibility; confirm these with the provider before sending proprietary slide images.
