from ppt_engine.production import (
    PageQualityScores, build_layout_plan, score_page, select_layout, layout_plan_to_design_ir,
)
from ppt_engine.intelligence import InformationGraph, InformationNode, InformationEdge
from ppt_engine.models import RelationType


def sample_graph():
    return InformationGraph(
        graph_id="g1",
        thesis="经营增长由客户、渠道和产品共同驱动",
        nodes=[
            InformationNode(id="n1", label="经营增长", kind="driver"),
            InformationNode(id="n2", label="客户经营", kind="driver"),
            InformationNode(id="n3", label="渠道效率", kind="driver"),
            InformationNode(id="n4", label="产品结构", kind="driver"),
        ],
        edges=[
            InformationEdge(source="n2", target="n1", relation=RelationType.CAUSALITY),
            InformationEdge(source="n3", target="n1", relation=RelationType.CAUSALITY),
            InformationEdge(source="n4", target="n1", relation=RelationType.CAUSALITY),
        ],
    )


def sample_catalog():
    return {"layouts": [{
        "id": "gen.test.driver",
        "name": "经营驱动因素",
        "semantic_families": ["causal"],
        "relations": ["causality"],
        "capacity": {"drivers": [2, 6]},
        "slots": ["headline_conclusion", "primary_driver", "supporting_drivers"],
        "density": "high",
    }]}


def test_weighted_page_score_and_blocking_risk():
    scores = PageQualityScores(
        logic=5, information_value=5, visual_hierarchy=4,
        density_efficiency=4, chart_or_diagram_quality=4,
        reusability=5, source_traceability=5,
    )
    review = score_page("deck:slide-1", scores, risks=["unreadable footnote"])
    assert review.weighted_total > 4
    assert review.decision == "revise"


def test_select_layout_uses_information_graph():
    result = select_layout(sample_graph(), sample_catalog())
    assert result.selected_pattern_id == "gen.test.driver"
    assert result.scores[0].total > 0.9


def test_layout_plan_preserves_unassigned_and_relation_review():
    graph = sample_graph()
    plan = build_layout_plan(graph, sample_catalog(), "gen.test.driver")
    assert plan.graph_id == "g1"
    assert plan.geometry_status == "needs_layout_resolution"
    assert len(plan.unresolved_relation_ids) == 3
    assert all(slot.geometry_token.startswith("gen.test.driver.") for slot in plan.slots)



def test_geometry_resolves_and_compiles_editable_design_ir():
    graph = sample_graph()
    geometry = {"layouts": {"gen.test.driver": {"slots": {
        "headline_conclusion": {"geometry": {"x": 0.5, "y": 0.2, "width": 12.0, "height": 0.6}},
        "primary_driver": {"geometry": {"x": 0.5, "y": 1.2, "width": 5.8, "height": 2.0}},
        "supporting_drivers": {"geometry": {"x": 6.5, "y": 1.2, "width": 6.0, "height": 4.0}, "arrangement": "grid", "max_items": 4}
    }}}}
    plan = build_layout_plan(graph, sample_catalog(), "gen.test.driver", geometry_catalog=geometry)
    assert plan.geometry_status == "resolved"
    ir = layout_plan_to_design_ir(graph, plan)
    assert ir.slide_id == "gen.test.driver"
    assert len(ir.nodes) == 5
    assert len(ir.relations) == 3
    assert all(node.geometry is not None for node in ir.nodes)
