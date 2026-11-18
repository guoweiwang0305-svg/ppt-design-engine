from ppt_engine.models import (
    Canvas, DesignConstraints, DesignIR, DesignNode, Geometry, Importance,
    PageMessage, SemanticRole,
)
from ppt_engine.optimization import optimize_layout


def make_ir(text="Short"):
    return DesignIR(
        deck_id="d1", slide_id="p011", canvas=Canvas(width=10, height=5),
        message=PageMessage(thesis="A clear thesis"),
        constraints=DesignConstraints(min_font_pt=12),
        nodes=[
            DesignNode(id="title", text=text, semantic_role=SemanticRole.THESIS,
                       importance=Importance.CRITICAL,
                       geometry=Geometry(x=0.5,y=0.3,width=9,height=0.5), font_size_pt=24),
            DesignNode(id="body", text="Evidence", semantic_role=SemanticRole.EVIDENCE,
                       geometry=Geometry(x=1,y=2,width=3,height=1), font_size_pt=16),
        ],
    )


def test_optimizer_returns_report_and_preserves_semantics():
    ir = make_ir()
    result = optimize_layout(ir, max_iterations=2)
    assert result.design_ir.slide_id == ir.slide_id
    assert result.design_ir.message.thesis == ir.message.thesis
    assert result.report.human_review_required is True
    assert result.report.decision in {"accept_for_human_review", "revise", "blocked"}


def test_optimizer_does_not_auto_move_overlapping_nodes():
    ir = make_ir()
    ir.nodes[1].geometry = Geometry(x=2,y=0.3,width=3,height=1)
    before = ir.nodes[1].geometry.model_dump()
    result = optimize_layout(ir)
    after = next(n for n in result.design_ir.nodes if n.id == "body").geometry.model_dump()
    assert before == after
    assert any(f.code == "element_overlap" for f in result.report.findings)


def test_optimizer_does_not_mutate_input():
    ir = make_ir("A very long title that should be checked for fit in a deliberately narrow title box " * 5)
    original = [n.font_size_pt for n in ir.nodes]
    optimize_layout(ir, max_iterations=2)
    assert [n.font_size_pt for n in ir.nodes] == original
