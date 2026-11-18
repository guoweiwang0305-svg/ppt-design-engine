import pytest
from pydantic import ValidationError
from ppt_engine.models import DesignIR


def sample():
    return {
        "deck_id": "demo", "slide_id": "s1",
        "canvas": {"width": 13.333, "height": 7.5, "unit": "in"},
        "message": {"thesis": "Revenue mix is changing"},
        "nodes": [{"id": "title", "text": "Revenue mix", "semantic_role": "thesis",
                   "importance": "critical", "geometry": {"x": 1, "y": 1, "width": 8, "height": 1}}],
        "relations": [], "constraints": {"density": "medium"}
    }


def test_design_ir_validates():
    ir = DesignIR.model_validate(sample())
    assert ir.nodes[0].id == "title"


def test_duplicate_node_ids_rejected():
    data = sample()
    data["nodes"].append(data["nodes"][0])
    with pytest.raises(ValidationError):
        DesignIR.model_validate(data)


def test_relation_unknown_node_rejected():
    data = sample()
    data["relations"] = [{"id": "r1", "from": "missing", "to": "title", "relation_type": "supports"}]
    with pytest.raises(ValidationError):
        DesignIR.model_validate(data)
