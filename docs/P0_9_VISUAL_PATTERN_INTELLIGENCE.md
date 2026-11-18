# P0.9 — Visual Pattern Intelligence

## Objective
Upgrade P0.8 structural-frequency mining into an explainable visual feature and similarity layer. Keep three concerns separate: semantic expression (what relationship), visual grammar (spatial expression), and style profile (palette, typography, iconography, chart conventions).

## Implemented
- Extract editable geometry/content features: approximate occupancy and whitespace, weighted visual center, focal dominance, image/text area, alignment regularity, typography levels/span, editable palette, chart/table/image counts.
- Transparent similarity weights: geometry 35%, composition 20%, typography 15%, color 15%, content mix 15%.
- Production adapter accepts only explicitly approved P0.8 patterns with explicit semantic mapping.
- Feature vector JSON Schema and Generali corporate style profile.

## Reference corpus
User uploads: AIA wealth-management deck (60 slides) and GCL + Alleanza deck (21 slides). They remain separate reference families: warm neutral/champagne-gold wealth education vs brand-red/white/charcoal corporate reporting.

Official external research: Generali Annual Integrated Report 2025, FY25 presentation, business model and strategy pages. The official strategy materials show interconnected strategic priorities, strategic foundations, growth/earnings/innovation pillars and operating metrics. The annual report's six-priority framework is an example of high-level logic mapped to a radial strategic system.

GCL deck narrative sequence: company identity → growth → geographic presence → key figures → market ranking → customer segmentation → tagging → acquisition → OMO → product system → health ecosystem → digital services. High element-count pages 11 and 17–19 should be evaluated for readability; frequency/density alone does not imply quality.

AIA deck supports customer needs, pension opportunity, product structure, regulation, participating-policy profit sources, risk management, rate-cycle context, asset preservation and wealth succession. It is not a Generali color reference.

## Generali profile boundary
See design_profiles/generali_corporate.json. This is an engineering approximation, not an official licensed brand book. Do not redraw the Generali lion emblem or use it as a generic decorative icon. Calibrate exact colors from original assets before production.

## Limitations
Geometry is editable-object bounding-box data, not pixel segmentation. Occupancy sums element areas and ignores overlap. Palette sampling excludes image pixels. Charts embedded as images may be missed. Similarity is deterministic, not a learned embedding. Connectors do not automatically imply semantic relationships.

## Next gates
Add human-labelled visual benchmark; chart grammar validation; semantic icon registry with licensing; render-based QA for font size, contrast, overlap, alignment and focal dominance.

The curated source index is stored at reference_data/insurance_reference_corpus_2026-11-18.json. It records the 60-slide AIA and 21-slide GCL decks as distinct evidence families, maps GCL page groups to candidate semantic/layout families, and links official Generali external references. It is an index/curation seed, not an automatically approved component library.
