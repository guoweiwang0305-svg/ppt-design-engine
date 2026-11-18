import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_every_generali_layout_slot_has_in_bounds_geometry():
    catalog = json.loads((ROOT / "visual_patterns/generali/insurance_layout_catalog.json").read_text(encoding="utf-8"))
    geometry = json.loads((ROOT / "visual_patterns/generali/layout_geometry.json").read_text(encoding="utf-8"))
    canvas = geometry["canvas"]
    assert set(catalog["layouts"][0])  # non-empty catalog
    assert set(x["id"] for x in catalog["layouts"]) == set(geometry["layouts"])
    for layout in catalog["layouts"]:
        slots = geometry["layouts"][layout["id"]]["slots"]
        assert set(layout["slots"]) == set(slots)
        for slot_id, spec in slots.items():
            g = spec["geometry"]
            assert g["x"] >= 0 and g["y"] >= 0
            assert g["width"] > 0 and g["height"] > 0
            assert g["x"] + g["width"] <= canvas["width"]
            assert g["y"] + g["height"] <= canvas["height"]
