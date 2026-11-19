from PIL import Image, ImageDraw
from ppt_engine.models import Canvas, DesignIR, DesignNode, Geometry, PageMessage, SemanticRole
from ppt_engine.image_critic import analyze_rendered_png


def make_ir():
    return DesignIR(
        deck_id="d", slide_id="visual", canvas=Canvas(width=10,height=5),
        message=PageMessage(thesis="A clear thesis"),
        nodes=[
            DesignNode(id="title",text="A clear thesis",semantic_role=SemanticRole.THESIS,
                geometry=Geometry(x=1,y=0.5,width=8,height=1),font_size_pt=30),
            DesignNode(id="body",text="Supporting evidence",semantic_role=SemanticRole.EVIDENCE,
                geometry=Geometry(x=1,y=2.5,width=8,height=1),font_size_pt=18),
        ],
    )


def test_raster_critic_maps_regions_and_visual_center(tmp_path):
    path=tmp_path/"slide.png"
    image=Image.new("RGB",(1000,500),"white")
    draw=ImageDraw.Draw(image)
    # Simulate rasterized text strokes within the two expected text regions.
    for x in range(120,500,35):
        draw.rectangle((x,80,x+18,95),fill="black")
    for x in range(120,700,28):
        draw.rectangle((x,300,x+12,312),fill="#333333")
    image.save(path)
    report=analyze_rendered_png(make_ir(),path)
    assert report.analyzed_regions==2
    assert report.global_ink_ratio>0
    assert report.region_metrics[0].ink_ratio>0
    assert 0 <= report.visual_center[0] <= 1
    assert report.width_px==1000


def test_raster_critic_flags_text_ink_touching_box_edge(tmp_path):
    path=tmp_path/"edge.png"
    image=Image.new("RGB",(1000,500),"white")
    draw=ImageDraw.Draw(image)
    draw.rectangle((100,50,400,65),fill="black")
    image.save(path)
    report=analyze_rendered_png(make_ir(),path)
    assert any(f.code=="rendered_text_near_region_edge" and "title" in f.node_ids for f in report.findings)


def test_raster_critic_flags_blank_render(tmp_path):
    path=tmp_path/"blank.png"
    Image.new("RGB",(1000,500),"white").save(path)
    report=analyze_rendered_png(make_ir(),path)
    assert any(f.code=="rendered_page_near_blank" for f in report.findings)


def test_raster_critic_handles_light_text_on_dark_panel(tmp_path):
    path=tmp_path/"dark.png"
    image=Image.new("RGB",(1000,500),"white")
    draw=ImageDraw.Draw(image)
    draw.rectangle((100,50,900,150),fill="#202020")
    for x in range(130,550,35):
        draw.rectangle((x,80,x+18,95),fill="white")
    image.save(path)
    report=analyze_rendered_png(make_ir(),path)
    title=next(metric for metric in report.region_metrics if metric.node_id=="title")
    assert title.ink_ratio>0
    assert title.status!="sparse"
