from PIL import Image
from ppt_engine.models import (
    Canvas, DesignIR, DesignNode, Geometry, PageMessage, SemanticRole,
)
import ppt_engine.quality_loop as quality_loop


def test_quality_loop_renders_then_runs_png_critic(tmp_path, monkeypatch):
    ir=DesignIR(
        deck_id="d1",slide_id="quality",canvas=Canvas(width=10,height=5),
        message=PageMessage(thesis="One clear point"),
        nodes=[DesignNode(id="title",text="One clear point",
            semantic_role=SemanticRole.THESIS,geometry=Geometry(x=1,y=0.5,width=8,height=0.8),
            font_size_pt=24)],
    )

    def fake_render(ir, path, ledger=None):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b"pptx")
        return path

    def fake_pdf(pptx, out):
        out.mkdir(parents=True,exist_ok=True)
        path=out/"quality.pdf"
        path.write_bytes(b"pdf")
        return path

    def fake_pngs(pdf, out):
        out.mkdir(parents=True,exist_ok=True)
        path=out/"slide-1.png"
        Image.new("RGB",(800,450),"white").save(path)
        return [path]

    monkeypatch.setattr(quality_loop,"render_pptx",fake_render)
    monkeypatch.setattr(quality_loop,"export_pdf",fake_pdf)
    monkeypatch.setattr(quality_loop,"export_pngs",fake_pngs)
    result=quality_loop.run_quality_loop(ir,tmp_path)
    assert result.pptx_path.endswith("quality.pptx")
    assert result.pdf_path.endswith("quality.pdf")
    assert result.png_paths
    assert result.critic.rendered_image_audit is not None
    assert result.critic.rendered_visual_critique is not None
    assert result.critic.rendered_visual_critique['analyzed_regions'] == 1
    assert result.design_ir.message.thesis=="One clear point"
