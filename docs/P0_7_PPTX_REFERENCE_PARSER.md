# P0.7 — PPTX Reference Parser

## What this milestone does

Command: ppt-engine parse-pptx input.pptx --output build/reference/reference.json

Reads editable PowerPoint files and emits one JSON record per slide.

### Extracted fields
- Canvas dimensions in EMU and inches.
- Per-element normalized geometry (x/y/width/height in 0..1 slide coordinates).
- Shape ID, name, type, rotation, z-order and group parent.
- Text, paragraph level/alignment, run-level font name/size/bold/italic/underline/color.
- Fill and line color/width/dash style where PowerPoint exposes them.
- Image dimensions and crop fractions.
- Connector bounding geometry and line style.

## Semantic safety

The parser does not equate visual proximity with business meaning. Native connectors are emitted as geometric evidence with semantic_relation=null and confidence 0.0. A later endpoint-resolution / VLM pass must determine whether a line is a real relationship, a decorative divider, or an arrow with business meaning.

Unlabeled shapes are retained as semantic candidates. They are not automatically discarded as decoration; a human or later classifier decides.

## Current boundaries
- No raster OCR or CV is performed.
- Connector start/end are currently represented by connector bounding-box corners; direction fidelity for diagonal/reversed connectors needs an OOXML-level enhancement.
- Group hierarchy is retained through parent group IDs, but group transforms are not yet flattened into child absolute coordinates.
- Theme color resolution, gradient stop extraction, shadows, effects, SmartArt internals, charts and embedded OLE objects need dedicated follow-up adapters.
- This milestone parses native elements; it does not yet reconstruct business semantics automatically.

## Validation

The test fixture creates a real editable PPTX with text, shape, run formatting and a connector, then verifies the extracted structure. It is a parser contract test, not a visual-quality test.