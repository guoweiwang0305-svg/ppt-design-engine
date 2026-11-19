from types import SimpleNamespace
from PIL import Image
import ppt_engine.ocr_critic as ocr
from ppt_engine.models import Canvas, DesignIR, DesignNode, Geometry, PageMessage, SemanticRole


def fixture():
    return DesignIR(deck_id="d",slide_id="ocr",canvas=Canvas(width=10,height=5),
        message=PageMessage(thesis="A clear thesis"),
        nodes=[DesignNode(id="title",text="A clear thesis",semantic_role=SemanticRole.THESIS,
            geometry=Geometry(x=1,y=0.5,width=8,height=1),font_size_pt=30)])


def test_ocr_reports_unavailable_without_tesseract(tmp_path,monkeypatch):
    image=tmp_path/"slide.png"
    Image.new("RGB",(1000,500),"white").save(image)
    monkeypatch.setattr(ocr.shutil,"which",lambda _:None)
    report=ocr.critique_rendered_text(fixture(),image)
    assert not report.available
    assert report.findings[0]["code"]=="ocr_unavailable"


def test_ocr_maps_recognized_words_to_design_region(tmp_path,monkeypatch):
    image=tmp_path/"slide.png"
    Image.new("RGB",(1000,500),"white").save(image)
    tsv=(
        "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
        "5\t1\t1\t1\t1\t1\t120\t80\t50\t20\t95\tA\n"
        "5\t1\t1\t1\t1\t2\t180\t80\t70\t20\t95\tclear\n"
        "5\t1\t1\t1\t1\t3\t260\t80\t80\t20\t95\tthesis\n"
    )
    monkeypatch.setattr(ocr.shutil,"which",lambda _: "/usr/bin/tesseract")
    monkeypatch.setattr(ocr.subprocess,"run",lambda *a,**k:SimpleNamespace(returncode=0,stdout=tsv,stderr=""))
    report=ocr.critique_rendered_text(fixture(),image)
    assert report.available
    assert report.regions[0].status=="matched"
    assert report.regions[0].token_coverage==1
