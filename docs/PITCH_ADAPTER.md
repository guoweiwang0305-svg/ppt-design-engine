# Pitch Adapter

Pitch is both an editor and collaboration backend, but not the design brain.

## Contract

Input:
- approved Design IR
- layout plan
- style tokens
- assets
- node IDs

Output:
- Pitch object mapping
- object IDs
- unsupported feature report
- render/export state

## Rules

1. Maintain `ir_node_id → pitch_block_id`.
2. Read existing page structure before modifying an existing slide.
3. Prefer updating mapped blocks over blindly appending objects.
4. Never emulate a key semantic feature silently when Pitch lacks it.
5. After write, re-read and validate object count/text completeness.
6. Pitch success response does not equal visual QA pass.
7. Native PPTX remains available as an independent renderer.

## Capability classes

- text
- shape
- image
- line
- color
- gradient
- shadow
- crop
- chart
- grouping
- notes
- export

Each adapter capability is explicit and versioned.
