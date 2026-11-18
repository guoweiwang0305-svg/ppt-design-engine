from pptx import Presentation
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.util import Inches, Pt

from ppt_engine.pptx_parser import parse_pptx


def test_parse_pptx_extracts_native_geometry_text_styles_and_connectors(tmp_path):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    title = slide.shapes.add_textbox(Inches(1), Inches(0.5), Inches(5), Inches(1))
    run = title.text_frame.paragraphs[0].add_run()
    run.text = "Growth strategy"
    run.font.name = "Arial"
    run.font.size = Pt(24)
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1), Inches(2), Inches(3), Inches(1))
    rect.text = "Channel"
    slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(4), Inches(2.5), Inches(6), Inches(2.5))
    source = tmp_path / "reference.pptx"
    prs.save(source)

    result = parse_pptx(source)
    parsed = result["slides"][0]
    assert parsed["element_count"] == 2
    assert parsed["connector_count"] == 1
    assert parsed["elements"][0]["text"] == "Growth strategy"
    assert parsed["elements"][0]["text_style"]["runs"][0]["font_size_pt"] == 24
    assert parsed["elements"][0]["bbox"]["x"] > 0
    assert parsed["connectors"][0]["semantic_relation"] is None
