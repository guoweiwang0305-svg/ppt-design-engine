# P0 Implementation Notes

## Implemented contracts

### Design IR
Pydantic models enforce unique node IDs, valid relation endpoints, positive dimensions and canvas bounds. The renderer intentionally refuses nodes without explicit geometry; no silent auto-layout is performed.

### Page state machine
Allowed happy path:

`planned → content_approved → design_approved → rendered → qa_passed → delivered`

Rework states increment the page version. Delivered pages are terminal. State is persisted as JSON using atomic replacement.

### DataLedger
A metric ID is registered once with value, unit, definition, source, time and context. Re-registering the same ID with changed content fails. Slide references are validated and repeated values can be compared across pages.

### Renderer
PPTX is editable. Current primitives: text, rectangle and ellipse. PDF export uses LibreOffice; PNG export uses Poppler `pdftoppm`. External binaries are runtime requirements, not Python packages.

## Known P0 boundaries

- Current renderer renders one IR page per invocation.
- Relation metadata is preserved in IR but connectors are not yet drawn.
- No automatic placement is attempted. Every rendered node needs geometry.
- A successful export is not a Visual QA pass.
- Cross-slide metric consistency helper currently accepts resolved per-slide values; the next increment will add a first-class slide DataRef schema.
- State persistence is atomic but not yet protected against concurrent writers.
