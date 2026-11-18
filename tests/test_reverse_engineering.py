from ppt_engine.models import RelationType
from ppt_engine.reverse_engineering import BoundingBox, Connector, PatternFeedback, PatternPreferenceProfile, ReferenceVisualPage, VisualElement, reconstruct_information_graph

def test_reconstruction_uses_connectors_but_not_decorations():
    page=ReferenceVisualPage(reference_id="ref",elements=[
        VisualElement(element_id="a",kind="text",text="Driver",bbox=BoundingBox(x=1,y=1,width=2,height=1)),
        VisualElement(element_id="b",kind="text",text="Outcome",bbox=BoundingBox(x=5,y=1,width=2,height=1)),
        VisualElement(element_id="decor",kind="shape",bbox=BoundingBox(x=0,y=0,width=1,height=1),is_decorative=True)],
        connectors=[Connector(connector_id="c",source_element="a",target_element="b",relation_hint=RelationType.CAUSALITY)])
    result=reconstruct_information_graph(page)
    assert len(result.information_graph.nodes)==2
    assert result.information_graph.edges[0].relation==RelationType.CAUSALITY
    assert "decor" in result.ignored_decorative_elements

def test_preference_learning_updates_profile():
    profile=PatternPreferenceProfile(profile_id="gcl")
    profile=profile.apply(PatternFeedback(pattern_id="network.ecosystem",reference_id="r1",decision="accept"))
    profile=profile.apply(PatternFeedback(pattern_id="matrix.segmentation",reference_id="r2",decision="reject"))
    assert profile.preference_adjustment("network.ecosystem")>0
    assert profile.preference_adjustment("matrix.segmentation")<0
