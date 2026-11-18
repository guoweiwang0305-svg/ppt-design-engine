from ppt_engine.models import DesignIR
from ppt_engine.renderer import render_pptx


def test_native_pptx_render(tmp_path):
    ir = DesignIR.model_validate({
        "deck_id": "demo", "slide_id": "s1",
        "message": {"thesis": "A clear thesis"},
        "nodes": [{"id": "title", "text": "A clear thesis", "semantic_role": "thesis",
                   "geometry": {"x": 1, "y": 1, "width": 8, "height": 1}}],
        "relations": []
    })
    target = render_pptx(ir, tmp_path / "test.pptx")
    assert target.exists() and target.stat().st_size > 1000
