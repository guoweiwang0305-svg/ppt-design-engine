# PPT Design Engine — Architecture 1.0

## 1. System boundary

The engine owns design reasoning, semantic representation, layout computation, rendering contracts and QA. External editors are adapters.

```
Project Control
      ↓
Content Architect
      ↓
Semantic Recognition
      ↓
Design IR
      ↓
Design Director
      ↓
3–5 Layout Candidates
      ↓
Layout Optimizer
      ↓
Approved Design IR
      ↓
Renderer Hub ──────→ Native PPTX
      │
      └──────────────→ Pitch
      ↓
Rendered PNG/PDF
      ↓
Visual QA
      ↓
Pass / Rework
```

## 2. AI vs deterministic responsibilities

### AI
- thesis extraction
- information relationship recognition
- narrative judgment
- visual grammar selection
- candidate rationale
- aesthetic trade-offs
- style application

### Deterministic code
- schema validation
- coordinate calculations
- collision/overflow detection
- data-ledger consistency
- font and canvas constraints
- renderer mapping
- file integrity
- visual regression infrastructure

## 3. Page lifecycle

`planned → content_approved → design_approved → rendered → qa_passed → delivered`

Failure states:

`content_rework | design_rework | render_rework | qa_rejected`

Every retry records issue, responsible stage, target version and acceptance condition.

## 4. Default canvas

16:9, 13.333 × 7.5 in. Layout uses a logical grid rather than unconstrained absolute positioning.

## 5. Rendering philosophy

Native PPTX is the formal delivery path. Pitch is a first-class optional backend. Both consume the same approved Design IR and must preserve node IDs for traceability.

Pitch must never be the design authority.
