import pytest
from pydantic import ValidationError
from ppt_engine.models import DesignIR
from ppt_engine.ledger import DataLedger, LedgerEntry
from ppt_engine.renderer import render_pptx


def test_metric_requires_data_ref():
    data = {
        "deck_id": "d", "slide_id": "s", "message": {"thesis": "Metric"},
        "nodes": [{"id": "m", "text": "hard-coded 100", "semantic_role": "metric",
                   "geometry": {"x": 1, "y": 1, "width": 4, "height": 1}}],
        "relations": []
    }
    with pytest.raises(ValidationError):
        DesignIR.model_validate(data)


def test_renderer_resolves_metric_from_ledger(tmp_path):
    ir = DesignIR.model_validate({
        "deck_id": "d", "slide_id": "s", "message": {"thesis": "Metric"},
        "nodes": [{"id": "m", "text": "", "semantic_role": "metric", "data_ref": "revenue",
                   "geometry": {"x": 1, "y": 1, "width": 4, "height": 1}}],
        "relations": []
    })
    ledger = DataLedger(entries={"revenue": LedgerEntry(
        id="revenue", value=120, unit="亿元", definition="Revenue",
        source="Annual report", time="2025"
    )})
    output = render_pptx(ir, tmp_path / "metric.pptx", ledger=ledger)
    assert output.exists()
