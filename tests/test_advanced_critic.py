from ppt_engine.models import (
    Canvas, DesignIR, DesignNode, DesignRelation, Geometry, Importance,
    PageMessage, RelationType, SemanticRole,
)
from ppt_engine.advanced_critic import (
    critique_slide, propose_collision_repairs, route_relations_orthogonal,
)


def fixture():
    return DesignIR(
        deck_id="d1", slide_id="p0112", canvas=Canvas(width=10,height=5),
        message=PageMessage(thesis="One clear conclusion"),
        nodes=[
            DesignNode(id="t",text="Conclusion",semantic_role=SemanticRole.THESIS,
                importance=Importance.CRITICAL,geometry=Geometry(x=1,y=0.3,width=8,height=0.7),font_size_pt=28),
            DesignNode(id="a",text="Driver",semantic_role=SemanticRole.EVIDENCE,
                geometry=Geometry(x=1,y=2,width=2,height=1),font_size_pt=16),
            DesignNode(id="b",text="Outcome",semantic_role=SemanticRole.EVIDENCE,
                geometry=Geometry(x=7,y=2,width=2,height=1),font_size_pt=16),
        ],
        relations=[DesignRelation(id="r1",**{"from":"a","to":"b"},relation_type=RelationType.CAUSALITY,direction="forward")],
    )


def test_orthogonal_route_avoids_obstacle():
    ir=fixture()
    ir.nodes.append(DesignNode(id="obstacle",text="Block",semantic_role=SemanticRole.CONTEXT,
        geometry=Geometry(x=4.1,y=1.7,width=1.8,height=1.6),font_size_pt=14))
    route=route_relations_orthogonal(ir)[0]
    assert route.status=="routed"
    assert len(route.points)>=3


def test_collision_suggestions_are_safe_and_non_mutating():
    ir=fixture()
    ir.nodes[2].geometry=Geometry(x=2,y=2,width=2,height=1)
    before=ir.nodes[2].geometry.model_dump()
    suggestions=propose_collision_repairs(ir)
    assert suggestions
    assert ir.nodes[2].geometry.model_dump()==before
    assert any(s.collision_free for s in suggestions)


def test_critic_reports_density_and_hierarchy():
    ir=fixture()
    for i in range(8):
        ir.nodes.append(DesignNode(id=f"x{i}",text="Supporting detail "*8,
            semantic_role=SemanticRole.CONTEXT,importance=Importance.LOW,
            geometry=Geometry(x=0.3+(i%4)*2.4,y=3.2+(i//4)*0.8,width=2,height=0.6),font_size_pt=12))
    report=critique_slide(ir)
    assert report.human_review_required
    assert report.page_split is not None
    assert report.routed_relations[0].status=="routed"
