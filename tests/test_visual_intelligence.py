from ppt_engine.mining import MinedPattern
from ppt_engine.visual_intelligence import extract_visual_features, compare_visual_features, adapt_approved_patterns

def sample():
    return {"source_file":"demo.pptx","slides":[{"slide_no":1,"density_heuristic":"high","text_element_count":2,"image_count":1,"chart_count":1,"table_count":0,"connector_count":1,"elements":[
      {"kind":"text_box","bbox":[.1,.1,.5,.2],"text":"Title","runs":[{"size_pt":30,"color":"#C00000"}]},
      {"kind":"text_box","bbox":[.1,.4,.4,.3],"text":"Body","runs":[{"size_pt":16,"color":"#222222"}]},
      {"kind":"picture","bbox":[.65,.2,.25,.4]}]}]}

def test_extract_features():
    f=extract_visual_features(sample())[0]
    assert f.reference_id=="demo.pptx:slide-1"
    assert f.image_area_ratio==.1
    assert f.typography_levels==2 and f.typography_span_pt==14
    assert 0<=f.whitespace_ratio<=1

def test_similarity_ranks_identical_higher():
    f=extract_visual_features(sample())[0]
    other=f.model_copy(update={"composition":"vertical"})
    scores=compare_visual_features([f],{"same":f,"other":other})
    assert scores[0].total>=scores[1].total

def test_adapter_requires_approval_and_mapping():
    p=MinedPattern(pattern_id="p1",name="p",family="horizontal",frequency=3,reference_slides=["a:slide-1"],expert_status="approved")
    pending=p.model_copy(update={"pattern_id":"p2","expert_status":"unreviewed"})
    mapping={"p1":{"semantic_families":["comparison"],"relation_types":["comparison"],"layouts":["two_column"],"visual_grammar_ref":"comparison.json"}}
    result=adapt_approved_patterns([p,pending],mapping)
    assert [x.pattern_id for x in result]==["p1"]
