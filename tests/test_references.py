import json
from ppt_engine.references import ReferenceAnnotation, export_reference_dataset
from ppt_engine.intelligence import InformationGraph, VisualGrammar
from ppt_engine.models import RelationType


def test_reference_annotation_roundtrip(tmp_path):
    record = ReferenceAnnotation(
        reference_id="ref-001", image_path="refs/slide.png",
        information_graph=InformationGraph(graph_id="g", thesis="Growth",
            nodes=[], edges=[]),
        visual_grammar=VisualGrammar(grammar_id="network", semantic_family="network",
            supported_relations=[RelationType.NETWORK], composition="clustered"),
        inferred_pattern_ids=["network.ecosystem"], confidence=0.8,
    )
    output = tmp_path / "dataset.json"
    export_reference_dataset([record], output)
    assert json.loads(output.read_text())[0]["reference_id"] == "ref-001"
