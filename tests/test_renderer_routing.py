from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from ppt_engine.models import (
    Canvas, DesignIR, DesignNode, DesignRelation, Geometry, PageMessage,
    RelationType, SemanticRole,
)
from ppt_engine.renderer import render_pptx


def test_renderer_uses_orthogonal_detour_around_obstacle(tmp_path):
    ir=DesignIR(
        deck_id="d1",slide_id="route",canvas=Canvas(width=10,height=5),
        message=PageMessage(thesis="Avoid obstacles"),
        nodes=[
            DesignNode(id="a",text="A",semantic_role=SemanticRole.EVIDENCE,
                geometry=Geometry(x=1,y=2,width=2,height=1)),
            DesignNode(id="b",text="B",semantic_role=SemanticRole.EVIDENCE,
                geometry=Geometry(x=7,y=2,width=2,height=1)),
            DesignNode(id="o",text="Obstacle",semantic_role=SemanticRole.CONTEXT,
                geometry=Geometry(x=4.1,y=1.7,width=1.8,height=1.6)),
        ],
        relations=[DesignRelation(id="r",**{"from":"a","to":"b"},relation_type=RelationType.CAUSALITY)],
    )
    output=render_pptx(ir,tmp_path/"routed.pptx")
    prs=Presentation(output)
    lines=[shape for shape in prs.slides[0].shapes if shape.shape_type==MSO_SHAPE_TYPE.LINE]
    assert len(lines)>=3
