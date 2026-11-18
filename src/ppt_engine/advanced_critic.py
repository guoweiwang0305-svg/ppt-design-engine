"""P0.11.2 advanced visual critic: geometry, hierarchy, routes and density."""
from __future__ import annotations
from typing import Literal
from pydantic import Field
from .models import DesignIR, StrictModel
from .visual_qa import audit_design_ir, audit_rendered_png


class GeometrySuggestion(StrictModel):
    node_id: str
    strategy: Literal["shift_right","shift_left","shift_down","shift_up","reflow_or_split"]
    proposed_x: float
    proposed_y: float
    rationale: str
    collision_free: bool = False


class RoutedRelation(StrictModel):
    relation_id: str
    points: list[tuple[float,float]] = Field(default_factory=list)
    status: Literal["routed","blocked","missing_endpoint"]
    reason: str = ""


class PageSplitSuggestion(StrictModel):
    reason: str
    primary_node_ids: list[str]
    secondary_node_ids: list[str]
    recommendation: str


class AdvancedCriticReport(StrictModel):
    slide_id: str
    decision: Literal["accept_for_human_review","revise","blocked"]
    findings: list[dict] = Field(default_factory=list)
    geometry_suggestions: list[GeometrySuggestion] = Field(default_factory=list)
    routed_relations: list[RoutedRelation] = Field(default_factory=list)
    page_split: PageSplitSuggestion | None = None
    rendered_image_audit: dict | None = None
    human_review_required: bool = True


def _overlap(a,b):
    return not (a.x+a.width <= b.x or b.x+b.width <= a.x or
                a.y+a.height <= b.y or b.y+b.height <= a.y)


def propose_collision_repairs(ir: DesignIR, margin: float=0.18) -> list[GeometrySuggestion]:
    """Return safe candidate translations. Never mutates DesignIR."""
    nodes=[n for n in ir.nodes if n.geometry is not None]
    result=[]
    for node in nodes:
        g=node.geometry
        colliders=[n for n in nodes if n.id != node.id and _overlap(g,n.geometry)]
        if not colliders:
            continue
        candidates=[
            ("shift_right",max(n.geometry.x+n.geometry.width for n in colliders)+margin,g.y),
            ("shift_left",min(n.geometry.x for n in colliders)-g.width-margin,g.y),
            ("shift_down",g.x,max(n.geometry.y+n.geometry.height for n in colliders)+margin),
            ("shift_up",g.x,min(n.geometry.y for n in colliders)-g.height-margin),
        ]
        found=False
        for strategy,x,y in candidates:
            if x < margin or y < margin or x+g.width > ir.canvas.width-margin or y+g.height > ir.canvas.height-margin:
                continue
            candidate=type(g)(x=x,y=y,width=g.width,height=g.height)
            if all(other.id==node.id or not _overlap(candidate,other.geometry) for other in nodes):
                result.append(GeometrySuggestion(node_id=node.id,strategy=strategy,
                    proposed_x=round(x,4),proposed_y=round(y,4),
                    rationale="Clears current collisions and respects canvas safe margins; apply only after checking reading order.",
                    collision_free=True))
                found=True
                break
        if not found:
            result.append(GeometrySuggestion(node_id=node.id,strategy="reflow_or_split",
                proposed_x=g.x,proposed_y=g.y,
                rationale="No collision-free translation fits the canvas; recompose the group or split the page.",
                collision_free=False))
    return result


def _segment_hits(a,b,r,pad):
    x1,y1=a; x2,y2=b
    l,t=r.x-pad,r.y-pad
    rr,bb=r.x+r.width+pad,r.y+r.height+pad
    if abs(y1-y2)<1e-8:
        return t<y1<bb and max(min(x1,x2),l)<min(max(x1,x2),rr)
    if abs(x1-x2)<1e-8:
        return l<x1<rr and max(min(y1,y2),t)<min(max(y1,y2),bb)
    return True


def route_relations_orthogonal(ir: DesignIR, clearance: float=0.12) -> list[RoutedRelation]:
    """Find the shortest clear route among four Manhattan candidates per edge."""
    by_id={n.id:n for n in ir.nodes}
    results=[]
    for edge in ir.relations:
        src,dst=by_id.get(edge.from_),by_id.get(edge.to)
        if src is None or dst is None or src.geometry is None or dst.geometry is None:
            results.append(RoutedRelation(relation_id=edge.id,status="missing_endpoint",reason="Endpoint geometry missing."))
            continue
        a,b=src.geometry,dst.geometry
        ac=(a.x+a.width/2,a.y+a.height/2); bc=(b.x+b.width/2,b.y+b.height/2)
        if abs(bc[0]-ac[0]) >= abs(bc[1]-ac[1]):
            start=(a.x+a.width if bc[0]>=ac[0] else a.x,ac[1])
            end=(b.x if bc[0]>=ac[0] else b.x+b.width,bc[1])
        else:
            start=(ac[0],a.y+a.height if bc[1]>=ac[1] else a.y)
            end=(bc[0],b.y if bc[1]>=ac[1] else b.y+b.height)
        obstacles=[n.geometry for n in ir.nodes if n.id not in (src.id,dst.id) and n.geometry]
        midx=(start[0]+end[0])/2; midy=(start[1]+end[1])/2
        candidates=[
            [start,(midx,start[1]),(midx,end[1]),end],
            [start,(start[0],midy),(end[0],midy),end],
            [start,(end[0],start[1]),end],
            [start,(start[0],end[1]),end],
        ]
        # Add detour channels just outside obstacle bounds; these are the
        # meaningful alternatives missing from a simple two-bend router.
        for obstacle in obstacles:
            for channel_y in (obstacle.y-clearance, obstacle.y+obstacle.height+clearance):
                if 0 <= channel_y <= ir.canvas.height:
                    candidates.append([start,(start[0],channel_y),(end[0],channel_y),end])
            for channel_x in (obstacle.x-clearance, obstacle.x+obstacle.width+clearance):
                if 0 <= channel_x <= ir.canvas.width:
                    candidates.append([start,(channel_x,start[1]),(channel_x,end[1]),end])
        valid=[]
        for pts in candidates:
            pts=[p for i,p in enumerate(pts) if i==0 or p!=pts[i-1]]
            if any(_segment_hits(p,q,o,clearance) for p,q in zip(pts,pts[1:]) for o in obstacles):
                continue
            length=sum(abs(q[0]-p[0])+abs(q[1]-p[1]) for p,q in zip(pts,pts[1:]))
            valid.append((length,pts))
        if not valid:
            results.append(RoutedRelation(relation_id=edge.id,status="blocked",
                reason="All candidate orthogonal paths intersect another node."))
        else:
            pts=min(valid,key=lambda x:x[0])[1]
            if edge.direction=="reverse": pts=list(reversed(pts))
            results.append(RoutedRelation(relation_id=edge.id,points=pts,status="routed"))
    return results


def _hierarchy(ir: DesignIR) -> list[dict]:
    findings=[]
    thesis=[n for n in ir.nodes if n.semantic_role.value=="thesis"]
    if len(thesis)!=1:
        findings.append({"code":"thesis_count","severity":"major","node_ids":[n.id for n in thesis],
            "diagnosis":f"Expected one thesis node, found {len(thesis)}.",
            "recommendation":"Make one primary page conclusion explicit."})
    else:
        t=thesis[0]
        competitors=[n for n in ir.nodes if n.id!=t.id and n.font_size_pt>=t.font_size_pt]
        if competitors:
            findings.append({"code":"hierarchy_competition","severity":"major","node_ids":[t.id]+[n.id for n in competitors],
                "diagnosis":"Non-thesis text matches or exceeds the thesis font size.",
                "recommendation":"Check whether these elements should compete with the page conclusion."})
    critical_metrics=[n for n in ir.nodes if n.semantic_role.value=="metric" and n.importance.value=="critical"]
    if critical_metrics and thesis and max(n.font_size_pt for n in critical_metrics)<thesis[0].font_size_pt*0.55:
        findings.append({"code":"key_metric_underweighted","severity":"minor","node_ids":[n.id for n in critical_metrics],
            "diagnosis":"Critical metrics are substantially smaller than the thesis.",
            "recommendation":"Consider stronger numeric emphasis without displacing the main conclusion."})
    return findings


def _layout_findings(ir: DesignIR) -> list[dict]:
    findings=[]
    margin=0.14
    nodes=[n for n in ir.nodes if n.geometry is not None and n.visual_type!="rect"]
    edge_nodes=[]
    for n in nodes:
        g=n.geometry
        if min(g.x,g.y,ir.canvas.width-(g.x+g.width),ir.canvas.height-(g.y+g.height)) < margin:
            edge_nodes.append(n.id)
    if edge_nodes:
        findings.append({"code":"unsafe_canvas_margin","severity":"minor","node_ids":edge_nodes,
            "diagnosis":f"{len(edge_nodes)} content elements sit within {margin:g} canvas units of an edge.",
            "recommendation":"Check clipping risk and restore a consistent safe margin unless intentional full-bleed composition is documented."})
    # Detect a near-aligned column whose left edges drift beyond normal tolerance.
    ordered=sorted(nodes,key=lambda n:n.geometry.x)
    for i in range(len(ordered)):
        group=[ordered[i]]
        for other in ordered[i+1:]:
            if abs(other.geometry.x-ordered[i].geometry.x) <= 0.28:
                group.append(other)
        if len(group)>=3:
            spread=max(n.geometry.x for n in group)-min(n.geometry.x for n in group)
            if 0.08 < spread <= 0.28:
                findings.append({"code":"alignment_drift","severity":"minor","node_ids":[n.id for n in group],
                    "diagnosis":f"Potential column alignment drift of {spread:.2f} canvas units across {len(group)} elements.",
                    "recommendation":"Snap elements to a shared left edge or document why the stagger is intentional."})
                break
    return findings


def _split_suggestion(ir: DesignIR) -> PageSplitSuggestion | None:
    nodes=[n for n in ir.nodes if n.geometry is not None]
    if len(nodes)<8: return None
    chars=sum(len(n.text) for n in nodes)
    area=sum(n.geometry.width*n.geometry.height for n in nodes)/(ir.canvas.width*ir.canvas.height)
    long=[n for n in nodes if len(n.text)>180]
    if chars<650 and area<0.68 and len(long)<2: return None
    primary=[n.id for n in nodes if n.importance.value in ("critical","high") or n.semantic_role.value=="thesis"]
    secondary=[n.id for n in nodes if n.id not in primary]
    if not secondary: return None
    return PageSplitSuggestion(reason=f"Density risk: {len(nodes)} elements, {chars} characters, summed-area proxy {area:.0%}.",
        primary_node_ids=primary,secondary_node_ids=secondary,
        recommendation="Keep thesis and decision-critical evidence on this page; move secondary detail to a follow-up page. Confirm narrative continuity before splitting.")


def critique_slide(ir: DesignIR, rendered_png: str | None=None) -> AdvancedCriticReport:
    findings=_hierarchy(ir)+_layout_findings(ir)
    qa=audit_design_ir(ir)
    for issue in qa.issues:
        findings.append({"code":issue.code,"severity":"blocker" if issue.severity=="error" else "major",
            "node_ids":issue.node_ids,"diagnosis":issue.message,
            "recommendation":"Resolve the geometry/font issue and rerun preflight."})
    image_audit=None
    if rendered_png:
        image_audit=audit_rendered_png(rendered_png).model_dump(mode="json")
        for issue in image_audit["issues"]:
            findings.append({"code":issue["code"],"severity":"blocker" if issue["severity"]=="error" else "minor",
                "node_ids":[],"diagnosis":issue["message"],
                "recommendation":"Inspect the rendered PNG at presentation size and rerender after repair."})
    routes=route_relations_orthogonal(ir)
    for route in routes:
        if route.status!="routed":
            findings.append({"code":"relation_route_"+route.status,"severity":"major",
                "node_ids":[],"diagnosis":route.reason or "Relation endpoints could not be routed.",
                "recommendation":"Adjust node positions or manually route this connector."})
    if any(f["severity"]=="blocker" for f in findings): decision="blocked"
    elif findings: decision="revise"
    else: decision="accept_for_human_review"
    return AdvancedCriticReport(slide_id=ir.slide_id,decision=decision,findings=findings,
        geometry_suggestions=propose_collision_repairs(ir),routed_relations=routes,
        page_split=_split_suggestion(ir),rendered_image_audit=image_audit,human_review_required=True)
