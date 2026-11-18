import json

from ppt_engine.mining import (
    PatternReview, apply_pattern_reviews, extract_slide_features,
    mine_patterns, save_pattern_review,
)


def _parsed(source, slide_number):
    return {
        "source_file": source,
        "slides": [{
            "slide_number": slide_number,
            "element_count": 2,
            "connector_count": 1,
            "elements": [
                {"kind": "text", "text": "Title", "bbox": {"x": 0.1, "y": 0.1, "width": 0.4, "height": 0.1},
                 "text_style": {"runs": [{"font_name": "Arial", "font_size_pt": 24, "color": "#112233"}]},
                 "fill": {"color": None}, "line": {"color": None}},
                {"kind": "shape", "text": "", "bbox": {"x": 0.6, "y": 0.2, "width": 0.2, "height": 0.2},
                 "text_style": {"runs": []}, "fill": {"color": "#FFFFFF"}, "line": {"color": None}},
            ],
            "connectors": [{"connector_id": "c1"}],
        }],
    }


def test_extract_features_and_mine_repeated_signatures(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps(_parsed("a.pptx", 1)), encoding="utf-8")
    b.write_text(json.dumps(_parsed("b.pptx", 3)), encoding="utf-8")
    features = extract_slide_features(json.loads(a.read_text(encoding="utf-8")))
    assert features[0].element_count == 2
    mined = mine_patterns([a, b], min_frequency=2)
    assert len(mined) == 1
    assert mined[0].frequency == 2
    assert mined[0].expert_status == "unreviewed"


def test_expert_review_is_append_only_and_applied(tmp_path):
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    a.write_text(json.dumps(_parsed("a.pptx", 1)), encoding="utf-8")
    b.write_text(json.dumps(_parsed("b.pptx", 1)), encoding="utf-8")
    patterns = mine_patterns([a, b], min_frequency=2)
    ledger = tmp_path / "reviews.jsonl"
    save_pattern_review(PatternReview(pattern_id=patterns[0].pattern_id, decision="accept", notes="clear hierarchy"), ledger)
    reviewed = apply_pattern_reviews(patterns, ledger)
    assert reviewed[0].expert_status == "approved"
