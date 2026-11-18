# P0.6 — Reference Reverse Engineering Engine

Goal: convert a strong reference slide from a picture or editable deck into reusable design knowledge.

## 1. Reference Visual Parser
Normalized contract covers text, shapes, images, icons, groups, bounding boxes, z-order, connectors, visual weight, decorative classification, hierarchy and confidence.

Current implementation is a deterministic contract plus connector-based baseline. It does not pretend to perform full OCR/CV extraction yet.

## 2. Information Graph Reconstruction
Explicit connectors become typed information edges. Decorative elements are excluded. Proximity alone never creates a business relationship. Every inferred relation carries confidence and source element IDs.

## 3. Visual Pattern Learning
PatternFeedback supports accept/reject/revise decisions, reason codes, notes and weight deltas. PatternPreferenceProfile converts those decisions into bounded ranking adjustments for Layout Optimizer.

## Adapter roadmap
1. Parse editable PPTX first whenever available.
2. Add OCR/layout extraction for raster slide images.
3. Add VLM semantic relation inference.
4. Validate geometry deterministically.
5. Add human correction UI.
6. Feed approved corrections into preference learning.

Design principle: learn information structure -> visual grammar -> layout family -> style expression, rather than blindly cloning screenshots.