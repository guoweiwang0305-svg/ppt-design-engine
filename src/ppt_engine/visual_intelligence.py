"""P0.9 visual pattern intelligence module.
from __future__ import annotations
import math, re
from collections import Counter
from typing import Any
from pydantic import Field
from .models import StrictModel
from .mining import MinedPattern

class VisualFeatureVector(StrictModel):
    reference_id: str
    source_file: str
    slide_number: int
    element_count: int
    text_count: int
    image_count: int
    chart_count: int
    table_count: int
    connector_count: int
    occupancy_ratio: float
    whitespace_ratio: float
    visual_center_x: float
    visual_center_y: float
    center_offset: float
    image_area_ratio: float
    text_area_ratio: float
    largest_element_share: float
    alignment_score: float
    typography_levels: int
    typography_span_pt: float
    dominant_colors: list[str] = Field(default_factory=list)
    color_count: int
    composition: str
    density: str
    feature_warnings: list[str] = Field(default_factory=list)

class SimilarityScore(StrictModel):
    reference_id: str
    pattern_id: str
    total: float
    geometry: float
    composition: float
    typography: float
    color: float
    content_mix: float
    explanation: list[str]

class ApprovedPatternAdapter(StrictModel):
    pattern_id: str
    name: str
    semantic_families: list[str]
    relation_types: list[str]
    min_nodes: int
    max_nodes: int
    density: str
    layouts: list[str]
    visual_grammar_ref: str
    tags: list[str]
    evidence_refs: list[str]
    expert_status: str = "approved"

def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))

def _sim(a: float, b: float, scale: float) -> float:
    return _clamp(1 - abs(a-b)/max(scale, 0.0001))

def _jaccard(a: list[str], b: list[str]) -> float:
    aa, bb = set(a), set(b)
    return len(aa & bb)/len(aa | bb) if aa or bb else 1.0

def _near_unique(values: list[float], tol: float = .035) -> int:
    groups = []
    for v in sorted(values):
        if not groups or abs(v-groups[-1]) > tol: groups.append(v)
    return len(groups)

def extract_visual_features(parsed: dict[str, Any]) -> list[VisualFeatureVector]:
    """Extract explainable geometry, whitespace, typography and palette features."""
    source = str(parsed.get("source_file", "unknown")); output = []
    for slide in parsed.get("slides", []):
        elems = [e for e in slide.get("elements", []) if isinstance(e.get("bbox"), list) and len(e["bbox"]) == 4]
        areas=[]; centers=[]; xs=[]; fonts=[]; colors=Counter(); text_area=0.; image_area=0.
        for e in elems:
            x,y,w,h = map(float,e["bbox"]); area=max(0.,w)*max(0.,h)
            areas.append(area); centers.append((x+w/2,y+h/2,max(area,.0001))); xs.append(x)
            if e.get("text"): text_area += area
            if e.get("kind")=="picture": image_area += area
            for run in e.get("runs",[]):
                if isinstance(run.get("size_pt"),(int,float)): fonts.append(float(run["size_pt"]))
                c=run.get("color")
                if isinstance(c,str) and re.fullmatch(r"#[0-9a-fA-F]{6}",c): colors[c.upper()] += max(area,.0001)
            for key in ("fill","line"):
                c=(e.get(key) or {}).get("color")
                if isinstance(c,str) and re.fullmatch(r"#[0-9a-fA-F]{6}",c): colors[c.upper()] += max(area,.0001)
        occ=_clamp(sum(areas)); total=sum(c[2] for c in centers)
        cx=sum(c[0]*c[2] for c in centers)/total if total else .5
        cy=sum(c[1]*c[2] for c in centers)/total if total else .5
        offset=math.sqrt((cx-.5)**2+(cy-.5)**2)/math.sqrt(.5)
        unique=sorted(set(round(v,1) for v in fonts)); n=len(elems)
        xspread=max((c[0] for c in centers),default=.5)-min((c[0] for c in centers),default=.5)
        yspread=max((c[1] for c in centers),default=.5)-min((c[1] for c in centers),default=.5)
        composition="sparse" if n<6 else "grid_or_distributed"
        if xspread>.6 and yspread<.35: composition="horizontal"
        elif yspread>.55 and xspread<.4: composition="vertical"
        elif offset>.28: composition="asymmetric"
        warnings=[]
        if not fonts: warnings.append("no_editable_font_size_data")
        if not elems: warnings.append("no_geometry_data")
        output.append(VisualFeatureVector(
            reference_id=f"{source}:slide-{slide.get('slide_no',0)}",source_file=source,
            slide_number=int(slide.get("slide_no",0)),element_count=n,
            text_count=int(slide.get("text_element_count",sum(bool(e.get("text")) for e in elems))),
            image_count=int(slide.get("image_count",0)),chart_count=int(slide.get("chart_count",0)),
            table_count=int(slide.get("table_count",0)),connector_count=int(slide.get("connector_count",0)),
            occupancy_ratio=round(occ,4),whitespace_ratio=round(1-occ,4),
            visual_center_x=round(cx,4),visual_center_y=round(cy,4),center_offset=round(offset,4),
            image_area_ratio=round(_clamp(image_area),4),text_area_ratio=round(_clamp(text_area),4),
            largest_element_share=round(max(areas,default=0)/max(sum(areas),.0001),4),
            alignment_score=round(_clamp(1-max(0,_near_unique(xs)-1)/max(1,len(xs)-1)),4),
            typography_levels=len(unique),typography_span_pt=round(max(fonts)-min(fonts),2) if fonts else 0.,
            dominant_colors=[c for c,_ in colors.most_common(8)],color_count=len(colors),
            composition=composition,density=str(slide.get("density_heuristic","unknown")),feature_warnings=warnings))
    return output

def compare_visual_features(features: list[VisualFeatureVector], exemplars: dict[str,VisualFeatureVector], top_k: int=10) -> list[SimilarityScore]:
    """Weighted, transparent similarity; not a learned visual embedding."""
    results=[]
    for f in features:
        for pid,r in exemplars.items():
            geo=sum([_sim(f.occupancy_ratio,r.occupancy_ratio,.8),_sim(f.center_offset,r.center_offset,.7),_sim(f.alignment_score,r.alignment_score,1.),_sim(f.largest_element_share,r.largest_element_share,.8)])/4
            comp=1. if f.composition==r.composition else .35
            typo=(_sim(f.typography_levels,r.typography_levels,6)+_sim(f.typography_span_pt,r.typography_span_pt,48))/2
            color=_jaccard(f.dominant_colors,r.dominant_colors)
            mix=(_sim(f.image_area_ratio,r.image_area_ratio,.7)+_sim(f.text_area_ratio,r.text_area_ratio,.7)+_sim(f.chart_count+f.table_count,r.chart_count+r.table_count,8))/3
            total=.35*geo+.20*comp+.15*typo+.15*color+.15*mix
            results.append(SimilarityScore(reference_id=f.reference_id,pattern_id=pid,total=round(total,4),geometry=round(geo,4),composition=round(comp,4),typography=round(typo,4),color=round(color,4),content_mix=round(mix,4),explanation=["geometry 35%: occupancy, visual center, alignment, focal dominance","composition 20%: geometric family","typography 15%: hierarchy levels and font span","color 15%: editable palette overlap","content mix 15%: image/text area and chart/table counts","Deterministic heuristic; not learned perceptual similarity"]))
    return sorted(results,key=lambda x:x.total,reverse=True)[:top_k]

def adapt_approved_patterns(patterns: list[MinedPattern], mapping: dict[str,dict[str,Any]]) -> list[ApprovedPatternAdapter]:
    """Only accepted P0.8 patterns with explicit semantic mapping enter retrieval."""
    out=[]
    for p in patterns:
        spec=mapping.get(p.pattern_id)
        if p.expert_status!="approved" or not spec: continue
        out.append(ApprovedPatternAdapter(pattern_id=p.pattern_id,name=p.name,semantic_families=spec["semantic_families"],relation_types=spec["relation_types"],min_nodes=int(spec.get("min_nodes",2)),max_nodes=int(spec.get("max_nodes",24)),density=spec.get("density","high"),layouts=spec["layouts"],visual_grammar_ref=spec["visual_grammar_ref"],tags=spec.get("tags",[]),evidence_refs=p.reference_slides))
    return out
