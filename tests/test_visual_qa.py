from ppt_engine.models import (
    Canvas, DesignConstraints, DesignIR, DesignNode, Geometry, Importance,
    PageMessage, SemanticRole,
)
from ppt_engine.visual_qa import audit_design_ir, audit_rendered_png


def make_ir():
    return DesignIR(
        deck_id="d1", slide_id="s1", canvas=Canvas(width=10, height=5),
        message=PageMessage(thesis="Test slide"),
        constraints=DesignConstraints(min_font_pt=14),
        nodes=[
            DesignNode(id="a", text="A", semantic_role=SemanticRole.THESIS,
                       importance=Importance.HIGH, geometry=Geometry(x=1,y=1,width=4,height=2),
                       font_size_pt=18),
            DesignNode(id="b", text="B", semantic_role=SemanticRole.EVIDENCE,
                       geometry=Geometry(x=3,y=1,width=4,height=2), font_size_pt=10),
        ],
    )


def test_preflight_detects_overlap_and_small_font():
    report = audit_design_ir(make_ir())
    codes = {issue.code for issue in report.issues}
    assert "element_overlap" in codes
    assert "font_below_minimum" in codes
    assert report.status == "review_required"
    assert report.human_review_required is True



def test_rendered_png_audit_reports_dimensions_and_pixel_metrics(tmp_path):
    from PIL import Image, ImageDraw
    path = tmp_path / "slide.png"
    image = Image.new("RGB", (800, 450), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 720, 360), fill="#C00000")
    image.save(path)
    report = audit_rendered_png(str(path))
    assert report.width_px == 800
    assert report.height_px == 450
    assert report.non_white_ratio > 0.4
    assert report.status == "review_required"
