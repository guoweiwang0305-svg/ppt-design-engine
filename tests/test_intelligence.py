import pytest
from ppt_engine.intelligence import InformationGraph, InformationNode, InformationEdge, PatternCandidate, rank_patterns
from ppt_engine.models import RelationType


def graph():
    return InformationGraph(
        graph_id="g1", thesis="Drivers produce growth",
        nodes=[InformationNode(id=str(i), label=f"n{i}") for i in range(6)],
        edges=[
            InformationEdge(source="0", target="1", relation=RelationType.CAUSALITY),
            InformationEdge(source="2", target="1", relation=RelationType.CAUSALITY),
            InformationEdge(source="1", target="3", relation=RelationType.SUPPORTS),
        ],
    )


def test_ranker_prefers_causal_pattern():
    causal = PatternCandidate(pattern_id="causal", name="causal", semantic_families=["causal"],
        relation_types=[RelationType.CAUSALITY, RelationType.SUPPORTS], min_nodes=4,
        max_nodes=12, density="high", layouts=["multi_driver_outcome"], visual_grammar_ref="g")
    matrix = PatternCandidate(pattern_id="matrix", name="matrix", semantic_families=["comparison"],
        relation_types=[RelationType.COMPARISON], min_nodes=4, max_nodes=12,
        density="high", layouts=["matrix"], visual_grammar_ref="m")
    ranked = rank_patterns(graph(), [matrix, causal], requested_density="high")
    assert ranked[0].pattern_id == "causal"


def test_invalid_graph_rejected_by_ranker():
    bad = graph()
    bad.edges[0].target = "missing"
    with pytest.raises(ValueError):
        rank_patterns(bad, [])
