# PPT Design Engine

A local-first, AI-assisted presentation design engine for high-end, information-dense, diagram-first business presentations.

## Product thesis

PPT Design Engine is not a template generator. It separates **design intelligence** from **rendering**:

`Content → Semantic Design IR → Design Director → Layout Candidates → Optimizer → Renderer → Visual QA → Delivery`

The core design model is renderer-independent. Pitch is supported as an editor/collaboration backend, while native PPTX is the primary delivery backend.

## Architecture

- **Content Architect** — research, evidence, narrative, page thesis.
- **Design Director** — autonomous visual/design decisions.
- **Layout Intelligence** — semantic layout generation and ranking.
- **Renderer Hub** — native PPTX + Pitch adapters.
- **Visual QA** — perceptual and deterministic checks.
- **Orchestrator** — state, versions, retries and acceptance.
- **Style DNA** — reusable visual systems such as GCL.

## Engineering principles

1. Logic before decoration.
2. Information relationship before template selection.
3. AI decides; deterministic code constrains and verifies.
4. Rendered output is the visual source of truth.
5. QA can reject a page.
6. Never solve density by shrinking type first.
7. Gradients and shadows are semantic tools, not automatic “premium” effects.
8. A layout candidate must be structurally different, not merely recolored.

## Initial roadmap

M0 foundation → M1 semantic Design IR → M2 layout intelligence → M3 native PPTX renderer → M4 Pitch adapter → M5 perceptual QA → M6 preference learning.

## Repository status

This repository is intentionally being built as a real engineering system. The first commit establishes the architecture contracts and GCL design DNA; implementation follows behind stable interfaces.
