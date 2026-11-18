# Architecture Decisions

## ADR-001 — Local-first
Core assets and execution remain local. Cloud services are optional providers, not system dependencies.

## ADR-002 — Design IR as source of truth
Neither Pitch nor PPTX is the canonical design representation.

## ADR-003 — Native PPTX + Pitch
Both are supported. Native PPTX is the formal delivery backend; Pitch is an editor/collaboration backend.

## ADR-004 — Design Director has design authority
Renderers implement approved decisions. They do not invent visual logic.

## ADR-005 — Rendered output is required for visual acceptance
Source/IR inspection alone cannot prove visual quality.

## ADR-006 — Template library is subordinate to semantic layout
Templates/components are retrieval resources, not the design decision system.

## ADR-007 — Preference learning is constrained
User preferences influence ranking weights but cannot override readability, semantic accuracy or brand constraints.
